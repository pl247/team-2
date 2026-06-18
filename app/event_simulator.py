"""
Built-in event simulator for the Machine Downtime Log application.
Generates realistic machine stoppage events for testing and demonstration.
"""
import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any
from .models import EventStream
from .database import SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventSimulator:
    """Simulates machine events for testing the downtime logging system."""
    
    def __init__(self, interval_seconds: int = 8):
        self.interval_seconds = max(1, interval_seconds)  # Minimum 1 second
        self.running = False
        self._task = None
        
        # Sample machine data for realistic simulation
        self.machines = [
            {"id": "CNC-001", "type": "CNC Mill"},
            {"id": "CNC-002", "type": "CNC Lathe"},
            {"id": "ROBOT-001", "type": "Assembly Robot"},
            {"id": "ROBOT-002", "type": "Welding Robot"},
            {"id": "PRESS-001", "type": "Hydraulic Press"},
            {"id": "PRESS-002", "type": "Stamping Press"},
            {"id": "CONVEYOR-001", "type": "Material Conveyor"},
            {"id": "CONVEYOR-002", "type": "Sorting Conveyor"},
            {"id": "PAINT-001", "type": "Paint Booth"},
            {"id": "PAINT-002", "type": "Drying Oven"},
        ]
        
        # Event types and descriptions
        self.event_types = ["start", "stop"]
        self.descriptions = [
            "Machine jammed due to material feed issue",
            "Operator initiated emergency stop",
            "Scheduled maintenance required",
            "Power fluctuation detected",
            "Tool wear exceeded threshold",
            "Coolant system malfunction",
            "Safety guard triggered",
            "Network communication loss",
            "Temperature sensor failure",
            "Hydraulic pressure low",
            "Material shortage detected",
            "Quality reject rate high",
            "Programming error in CNC code",
            "Air supply pressure drop",
            "Vision system calibration needed"
        ]
    
    async def start(self):
        """Start the event simulation."""
        if self.running:
            logger.warning("Event simulator is already running")
            return
            
        self.running = True
        logger.info(f"Starting event simulator with {self.interval_seconds}s interval")
        
        # Start the simulation task
        self._task = asyncio.create_task(self._simulate_events())
    
    async def stop(self):
        """Stop the event simulation."""
        if not self.running:
            logger.warning("Event simulator is not running")
            return
            
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Event simulator stopped")
    
    async def _simulate_events(self):
        """Main simulation loop."""
        while self.running:
            try:
                # Generate a random event
                event = self._generate_event()
                
                # Save to database
                await self._save_event(event)
                
                # Wait for the specified interval
                await asyncio.sleep(self.interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event simulation: {e}")
                # Continue simulation despite errors
                await asyncio.sleep(min(self.interval_seconds, 5))  # Shorter delay on error
    
    def _generate_event(self) -> Dict[str, Any]:
        """Generate a single random machine event."""
        machine = random.choice(self.machines)
        event_type = random.choice(self.event_types)
        description = random.choice(self.descriptions)
        
        # Calculate latency (simulate realistic network delay)
        # On Cisco Secure AI Factory's high-performance network, this should be very low
        latency_ms = random.randint(1, 10)  # 1-10ms for on-prem network
        
        return {
            "machine_id": machine["id"],
            "machine_type": machine["type"],
            "timestamp": datetime.utcnow(),
            "event_type": event_type,
            "description": description,
            "latency_ms": latency_ms
        }
    
    async def _save_event(self, event_data: Dict[str, Any]):
        """Save an event to the database."""
        try:
            # Create a new database session for this operation
            db = SessionLocal()
            try:
                # Create EventStream instance
                event = EventStream(**event_data)
                
                # Add to session and commit
                db.add(event)
                db.commit()
                
                logger.debug(f"Saved simulated event: {event_data['machine_id']} - {event_data['event_type']}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to save simulated event: {e}")
            # Don't re-raise - we want the simulation to continue


# Global simulator instance
simulator = EventSimulator()