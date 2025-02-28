"""
Event system for OpenHands ACI.

This module provides an event system that allows components to subscribe to and
trigger events, enabling loose coupling between different parts of the system.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions
EventHandler = Callable[..., Any]
EventFilter = Callable[[str, Dict[str, Any]], bool]


class EventSystem:
    """Event system for OpenHands ACI.
    
    This class provides methods for subscribing to and triggering events.
    """
    
    def __init__(self):
        """Initialize the event system."""
        self._handlers: Dict[str, List[Tuple[EventHandler, Optional[EventFilter]]]] = {}
        self._all_handlers: List[Tuple[EventHandler, Optional[EventFilter]]] = []
    
    def subscribe(self, event_name: str, handler: EventHandler, 
                 event_filter: Optional[EventFilter] = None) -> None:
        """Subscribe to an event.
        
        Args:
            event_name: Name of the event to subscribe to
            handler: Function to call when the event is triggered
            event_filter: Optional filter function to determine if the handler should be called
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        
        self._handlers[event_name].append((handler, event_filter))
        logger.debug(f"Subscribed handler to event: {event_name}")
    
    def subscribe_all(self, handler: EventHandler, 
                     event_filter: Optional[EventFilter] = None) -> None:
        """Subscribe to all events.
        
        Args:
            handler: Function to call when any event is triggered
            event_filter: Optional filter function to determine if the handler should be called
        """
        self._all_handlers.append((handler, event_filter))
        logger.debug("Subscribed handler to all events")
    
    def unsubscribe(self, event_name: str, handler: EventHandler) -> bool:
        """Unsubscribe from an event.
        
        Args:
            event_name: Name of the event to unsubscribe from
            handler: Handler function to remove
            
        Returns:
            True if the handler was removed, False otherwise
        """
        if event_name not in self._handlers:
            return False
        
        initial_count = len(self._handlers[event_name])
        self._handlers[event_name] = [
            (h, f) for h, f in self._handlers[event_name] if h != handler
        ]
        
        removed = initial_count > len(self._handlers[event_name])
        if removed:
            logger.debug(f"Unsubscribed handler from event: {event_name}")
        
        return removed
    
    def unsubscribe_all(self, handler: EventHandler) -> bool:
        """Unsubscribe from all events.
        
        Args:
            handler: Handler function to remove
            
        Returns:
            True if the handler was removed from any event, False otherwise
        """
        # Remove from specific events
        removed = False
        for event_name in self._handlers:
            initial_count = len(self._handlers[event_name])
            self._handlers[event_name] = [
                (h, f) for h, f in self._handlers[event_name] if h != handler
            ]
            if initial_count > len(self._handlers[event_name]):
                removed = True
        
        # Remove from all events handler
        initial_count = len(self._all_handlers)
        self._all_handlers = [(h, f) for h, f in self._all_handlers if h != handler]
        if initial_count > len(self._all_handlers):
            removed = True
        
        if removed:
            logger.debug("Unsubscribed handler from all events")
        
        return removed
    
    def trigger(self, event_name: str, **kwargs) -> List[Any]:
        """Trigger an event.
        
        Args:
            event_name: Name of the event to trigger
            **kwargs: Arguments to pass to the event handlers
            
        Returns:
            List of results from the event handlers
        """
        results = []
        
        # Call specific event handlers
        if event_name in self._handlers:
            for handler, event_filter in self._handlers[event_name]:
                try:
                    # Apply filter if provided
                    if event_filter is None or event_filter(event_name, kwargs):
                        results.append(handler(event_name=event_name, **kwargs))
                except Exception as e:
                    logger.error(f"Error in event handler for {event_name}: {str(e)}")
        
        # Call handlers subscribed to all events
        for handler, event_filter in self._all_handlers:
            try:
                # Apply filter if provided
                if event_filter is None or event_filter(event_name, kwargs):
                    results.append(handler(event_name=event_name, **kwargs))
            except Exception as e:
                logger.error(f"Error in all-events handler for {event_name}: {str(e)}")
        
        logger.debug(f"Triggered event: {event_name} with {len(results)} handlers")
        return results
    
    def get_event_names(self) -> Set[str]:
        """Get the names of all events that have handlers.
        
        Returns:
            Set of event names
        """
        return set(self._handlers.keys())
    
    def get_handler_count(self, event_name: Optional[str] = None) -> int:
        """Get the number of handlers for an event.
        
        Args:
            event_name: Name of the event to get handler count for, or None for all events
            
        Returns:
            Number of handlers
        """
        if event_name is None:
            # Count all handlers
            count = len(self._all_handlers)
            for handlers in self._handlers.values():
                count += len(handlers)
            return count
        
        # Count handlers for specific event
        if event_name not in self._handlers:
            return 0
        return len(self._handlers[event_name])


# Global event system instance
event_system = EventSystem()

# Convenience functions that use the global event system
def subscribe(event_name: str, handler: EventHandler, 
             event_filter: Optional[EventFilter] = None) -> None:
    """Subscribe to an event using the global event system."""
    event_system.subscribe(event_name, handler, event_filter)

def subscribe_all(handler: EventHandler, 
                 event_filter: Optional[EventFilter] = None) -> None:
    """Subscribe to all events using the global event system."""
    event_system.subscribe_all(handler, event_filter)

def unsubscribe(event_name: str, handler: EventHandler) -> bool:
    """Unsubscribe from an event using the global event system."""
    return event_system.unsubscribe(event_name, handler)

def unsubscribe_all(handler: EventHandler) -> bool:
    """Unsubscribe from all events using the global event system."""
    return event_system.unsubscribe_all(handler)

def trigger(event_name: str, **kwargs) -> List[Any]:
    """Trigger an event using the global event system."""
    return event_system.trigger(event_name, **kwargs)

def get_event_names() -> Set[str]:
    """Get the names of all events that have handlers using the global event system."""
    return event_system.get_event_names()

def get_handler_count(event_name: Optional[str] = None) -> int:
    """Get the number of handlers for an event using the global event system."""
    return event_system.get_handler_count(event_name)