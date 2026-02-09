"""
Supply Agent: Manages supply chain and resource delivery
Handles inventory, delivery prioritization, and reallocation
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from ..agents.base_agent import BaseAgent
from ..config.constants import (
    DELIVERY_BASE_TIME,
    PRIORITY_DELIVERY_MULTIPLIER,
    AGENT_TYPE_SUPPLY,
)


class SupplyAgent(BaseAgent):
    """
    Supply chain agent that manages inventory and delivery prioritization.
    Makes decisions on resource allocation and delivery routing.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        location: Tuple[float, float],
        food_units: int = 500,
        water_units: int = 1000,
        oxygen_units: int = 200,
        medicine_units: int = 300,
        delivery_vehicles: int = 4,
    ):
        super().__init__(agent_id, AGENT_TYPE_SUPPLY, name)
        
        self.location = location
        
        # Inventory
        self.inventory = {
            "food": food_units,
            "water": water_units,
            "oxygen": oxygen_units,
            "medicine": medicine_units,
        }
        
        # Delivery resources
        self.delivery_vehicles = delivery_vehicles
        self.vehicles_available = delivery_vehicles
        
        # Active deliveries
        self.active_deliveries: List[Dict] = []
        self.completed_deliveries: List[Dict] = []
        
        # Pending requests (priority queue)
        self.pending_requests: List[Dict] = []
    
    @property
    def has_available_vehicles(self) -> bool:
        """Check if delivery vehicles are available"""
        return self.vehicles_available > 0
    
    def get_inventory_status(self, supply_type: str) -> str:
        """Get status level for a supply type"""
        quantity = self.inventory.get(supply_type, 0)
        initial = {"food": 500, "water": 1000, "oxygen": 200, "medicine": 300}
        
        ratio = quantity / initial.get(supply_type, 1)
        if ratio < 0.2:
            return "critical"
        elif ratio < 0.4:
            return "low"
        else:
            return "ok"
    
    def get_state(self) -> Dict[str, Any]:
        """Return current state for dashboard/API"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "location": self.location,
            "inventory": self.inventory,
            "inventory_status": {
                k: self.get_inventory_status(k) for k in self.inventory
            },
            "delivery_vehicles": self.delivery_vehicles,
            "vehicles_available": self.vehicles_available,
            "active_deliveries": len(self.active_deliveries),
            "pending_requests": len(self.pending_requests),
            "completed_deliveries": len(self.completed_deliveries),
        }
    
    def generate_message(self) -> Dict[str, Any]:
        """Generate status message for negotiation"""
        message = self.get_base_message()
        message.update({
            "message_type": "status_update",
            "current_capacity": {
                "inventory": self.inventory.copy(),
                "vehicles_available": self.vehicles_available,
            },
            "requests": [],
            "offers": self._generate_offers(),
            "priority_score": self.calculate_priority_score(),
        })
        return message
    
    def _generate_offers(self) -> List[Dict]:
        """Generate supply offers based on inventory"""
        offers = []
        for supply_type, quantity in self.inventory.items():
            if quantity > 0 and self.has_available_vehicles:
                offers.append({
                    "resource": supply_type,
                    "quantity_available": quantity,
                    "delivery_time": DELIVERY_BASE_TIME,
                })
        return offers
    
    def receive_message(self, message: Dict[str, Any]) -> None:
        """Process incoming message"""
        msg_type = message.get("message_type", "")
        
        if msg_type == "resource_request":
            self._handle_resource_request(message)
        elif msg_type == "priority_override":
            self._handle_priority_override(message)
    
    def _handle_resource_request(self, message: Dict):
        """Handle incoming resource request from hospital"""
        request = {
            "requester_id": message.get("agent_id"),
            "requester_location": message.get("location"),
            "supply_type": message.get("resource"),
            "quantity": message.get("quantity", 0),
            "urgency": message.get("urgency", "medium"),
            "timestamp": datetime.now(),
        }
        self.pending_requests.append(request)
        self._sort_requests_by_priority()
    
    def _handle_priority_override(self, message: Dict):
        """Handle government priority override"""
        # Bump up priority for specified requests
        pass
    
    def _sort_requests_by_priority(self):
        """Sort pending requests by urgency"""
        urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.pending_requests.sort(
            key=lambda r: urgency_order.get(r.get("urgency", "medium"), 2)
        )
    
    def allocate_supply(self, supply_type: str, quantity: int, destination_id: str, destination_location: Tuple) -> Optional[Dict]:
        """Allocate supplies for delivery"""
        available = self.inventory.get(supply_type, 0)
        
        if available < quantity or not self.has_available_vehicles:
            return None
        
        # Deduct from inventory
        self.inventory[supply_type] -= quantity
        self.vehicles_available -= 1
        
        # Calculate delivery time
        distance = self._calculate_distance(self.location, destination_location)
        base_time = (distance / 40) * 60  # Assume 40 km/h
        
        delivery = {
            "id": f"delivery_{len(self.active_deliveries):03d}",
            "supply_type": supply_type,
            "quantity": quantity,
            "destination_id": destination_id,
            "destination_location": destination_location,
            "eta_minutes": base_time,
            "started_at": datetime.now(),
            "status": "in_transit",
        }
        
        self.active_deliveries.append(delivery)
        
        self.log_action("supply_allocated", {
            "delivery_id": delivery["id"],
            "supply_type": supply_type,
            "quantity": quantity,
            "destination": destination_id,
        })
        
        return delivery
    
    def _calculate_distance(self, from_loc: Tuple, to_loc: Tuple) -> float:
        """Calculate distance between two points"""
        import math
        return math.sqrt(
            (to_loc[0] - from_loc[0])**2 + 
            (to_loc[1] - from_loc[1])**2
        )
    
    def process_pending_requests(self) -> List[Dict]:
        """Process pending requests and create allocations"""
        allocations = []
        
        processed = []
        for request in self.pending_requests:
            if not self.has_available_vehicles:
                break
            
            supply_type = request.get("supply_type")
            quantity = min(request.get("quantity", 0), self.inventory.get(supply_type, 0))
            
            if quantity > 0:
                allocation = self.allocate_supply(
                    supply_type,
                    quantity,
                    request.get("requester_id"),
                    request.get("requester_location", (50, 50))
                )
                if allocation:
                    allocations.append(allocation)
                    processed.append(request)
        
        # Remove processed requests
        for req in processed:
            self.pending_requests.remove(req)
        
        return allocations
    
    def update(self, tick: int) -> List[Dict[str, Any]]:
        """Update supply agent state for a simulation tick"""
        actions = []
        
        # Update active deliveries
        completed = []
        for delivery in self.active_deliveries:
            delivery["eta_minutes"] = max(0, delivery["eta_minutes"] - 5)
            
            if delivery["eta_minutes"] <= 0:
                delivery["status"] = "completed"
                completed.append(delivery)
                self.vehicles_available += 1
                
                actions.append({
                    "type": "delivery_completed",
                    "delivery_id": delivery["id"],
                    "destination": delivery["destination_id"],
                    "supply_type": delivery["supply_type"],
                    "quantity": delivery["quantity"],
                })
        
        # Move completed deliveries
        for delivery in completed:
            self.active_deliveries.remove(delivery)
            self.completed_deliveries.append(delivery)
        
        self.last_updated = datetime.now()
        return actions
    
    def calculate_priority_score(self) -> float:
        """Calculate priority score for negotiation"""
        # Supply agent has moderate priority
        score = 0.4
        
        # Increase if low on critical supplies
        if self.get_inventory_status("oxygen") == "critical":
            score += 0.2
        if self.get_inventory_status("medicine") == "critical":
            score += 0.1
        
        return min(1.0, score)
