import asyncio
import inspect
import traceback
import weakref
from typing import Callable, Any
from appPublic.log import debug, error, exception, warning


class WeakCallback:

	def __init__(self, func: Callable):

		self._is_coroutine = inspect.iscoroutinefunction(func)

		if inspect.ismethod(func):
			self._ref = weakref.WeakMethod(func)
		else:
			self._ref = weakref.ref(func)

		self._hash = hash(func)

	@property
	def is_coroutine(self):
		return self._is_coroutine

	def get(self):
		return self._ref()

	def __eq__(self, other):
		return isinstance(other, WeakCallback) and self._hash == other._hash

	def __hash__(self):
		return self._hash


class EventDispatcher:

	def __init__(
		self,
		*,
		continue_on_error=True,
		log_traceback=True,
		handler_timeout=None,
		error_handler=None,
	):

		self._events = {}

		self.continue_on_error = continue_on_error
		self.log_traceback = log_traceback
		self.handler_timeout = handler_timeout
		self.error_handler = error_handler

	def bind(self, event_name: str, func: Callable):

		if event_name not in self._events:
			self._events[event_name] = set()

		self._events[event_name].add(WeakCallback(func))

	def unbind(self, event_name: str, func: Callable):

		if event_name not in self._events:
			return

		target = WeakCallback(func)

		self._events[event_name] = {
			cb for cb in self._events[event_name]
			if cb != target
		}

		if not self._events[event_name]:
			del self._events[event_name]

	async def _run_error_handler(
		self,
		event_name,
		func,
		exc,
	):

		if not self.error_handler:
			return

		try:

			if inspect.iscoroutinefunction(self.error_handler):
				await self.error_handler(
					event_name,
					func,
					exc,
				)
			else:
				self.error_handler(
					event_name,
					func,
					exc,
				)

		except Exception as e:
			print(f"[EventDispatcher] error_handler failed: {e}")

	async def _execute_handler(
		self,
		cb,
		event_name,
		data,
	):

		func = cb.get()

		if func is None:
			return False

		try:

			if cb.is_coroutine:

				coro = func(data)

				if self.handler_timeout:
					await asyncio.wait_for(
						coro,
						timeout=self.handler_timeout,
					)
				else:
					await coro

			else:

				if self.handler_timeout:

					await asyncio.wait_for(
						asyncio.to_thread(func, data),
						timeout=self.handler_timeout,
					)

				else:
					func(data)

			return True

		except Exception as e:
			debug(
				f"[EventDispatcher] "
				f"handler failed: "
				f"event={event_name}, "
				f"handler={func}"
			)

			if self.log_traceback:
				debug(f'{traceback.format_exc()}')
				# traceback.print_exc()

			await self._run_error_handler(
				event_name,
				func,
				e,
			)

			if not self.continue_on_error:
				raise

			return True

	async def dispatch(
		self,
		event_name: str,
		data: Any = None,
	):

		if event_name not in self._events:
			return

		dead_callbacks = []

		for cb in list(self._events[event_name]):

			func = cb.get()

			if func is None:
				dead_callbacks.append(cb)
				continue

			await self._execute_handler(
				cb,
				event_name,
				data,
			)

		for cb in dead_callbacks:
			self._events[event_name].discard(cb)

		if (
			event_name in self._events
			and not self._events[event_name]
		):
			del self._events[event_name]
