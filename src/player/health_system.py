class HealthSystem:
    def __init__(self, max_health=100):
        """Initialize the health system with maximum health"""
        self.max_health = max_health
        self.current_health = max_health
        self.is_alive = True
    
    def take_damage(self, damage):
        """Apply damage to the health system"""
        self.current_health = max(0, self.current_health - damage)
        if self.current_health <= 0:
            self.is_alive = False
        return self.is_alive
    
    def heal(self, amount):
        """Restore health by specified amount"""
        self.current_health = min(self.max_health, self.current_health + amount)
        if self.current_health > 0:
            self.is_alive = True
    
    def get_health_percentage(self):
        """Calculate and return current health percentage"""
        return self.current_health / self.max_health
    
    def is_full_health(self):
        """Check if health is at maximum"""
        return self.current_health == self.max_health