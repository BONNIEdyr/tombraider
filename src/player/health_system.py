class HealthSystem:
    def __init__(self, max_health=100):
        self.max_health = max_health
        self.current_health = max_health
        self.is_alive = True
    
    def take_damage(self, damage):
        """受到伤害"""
        self.current_health = max(0, self.current_health - damage)
        if self.current_health <= 0:
            self.is_alive = False
        return self.is_alive
    
    def heal(self, amount):
        """恢复生命值"""
        self.current_health = min(self.max_health, self.current_health + amount)
        if self.current_health > 0:
            self.is_alive = True
    
    def get_health_percentage(self):
        """获取生命值百分比"""
        return self.current_health / self.max_health
    
    def is_full_health(self):
        """生命值是否已满"""
        return self.current_health == self.max_health