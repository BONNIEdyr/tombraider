from .base_item import Item

class Gun(Item):
    def __init__(self):
        super().__init__("Gun", "uncommon", "assets/items/gun.png")
        self.ammo_amount = 15
    
    def apply_effect(self, player):
        """Add ammo to player"""
        player.ammo = min(player.max_ammo, player.ammo + self.ammo_amount)
        return f"拾取了枪支！获得{self.ammo_amount}发子弹"

class Ammo(Item):
    def __init__(self):
        super().__init__("Ammo", "common", "assets/items/ammo.png")
        self.ammo_amount = 10
    
    def apply_effect(self, player):
        """Add ammo to player"""
        player.ammo = min(player.max_ammo, player.ammo + self.ammo_amount)
        return f"拾取了弹药包！获得{self.ammo_amount}发子弹"

class ExtendedMagazine(Item):
    def __init__(self):
        super().__init__("Extended Magazine", "rare", "assets/items/magazine.png")
        self.capacity_increase = 10
    
    def apply_effect(self, player):
        """Increase player's max ammo capacity"""
        player.max_ammo += self.capacity_increase
        return f"拾取了扩容弹匣！最大子弹容量增加{self.capacity_increase}"

class EnhancedBullets(Item):
    def __init__(self):
        super().__init__("Enhanced Bullets", "epic", "assets/items/bullets.png")
        self.damage_increase = 5
    
    def apply_effect(self, player):
        """Increase player's bullet damage"""
        if hasattr(player, 'bullet_damage'):
            player.bullet_damage += self.damage_increase
        return f"拾取了强化弹头！子弹伤害增加{self.damage_increase}"
