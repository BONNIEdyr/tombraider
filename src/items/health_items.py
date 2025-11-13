from .base_item import Item

class Medkit(Item):
    def __init__(self):
        super().__init__("Medkit", "rare", "assets/items/medkit.png")
    
    def apply_effect(self, player):
        """Heal the player by 50% of max health"""
        heal_amount = player.health_system.max_health * 0.5
        player.heal(heal_amount)
        return f"拾取了急救包！恢复{heal_amount}点生命值"

class Food(Item):
    def __init__(self):
        super().__init__("Food", "uncommon", "assets/items/food.png")
    
    def apply_effect(self, player):
        """Heal the player by 20% of max health"""
        heal_amount = player.health_system.max_health * 0.2
        player.heal(heal_amount)
        return f"拾取了食物！恢复{heal_amount}点生命值"
