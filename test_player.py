import pygame as pg
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from player.player import Player

def main():
    
    pg.init()
    screen = pg.display.set_mode((800, 600))
    pg.display.set_caption("玩家角色测试 - 按H治疗, 按T受伤, 空格射击")
    clock = pg.time.Clock()
    
    # 创建玩家实例
    player = Player(400, 300)
    
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    player.shoot()
                    print(f"发射子弹! 当前子弹数: {len(player.bullets)}")
                elif event.key == pg.K_h:
                    player.heal(20)
                    print(f"治疗! 当前生命值: {player.health_system.current_health}")
                elif event.key == pg.K_t:
                    player.take_damage(10)
                    print(f"受伤! 当前生命值: {player.health_system.current_health}")
        
        # 获取按键状态
        keys = pg.key.get_pressed()
        
        # 更新玩家
        player.update(keys, 800, 600)
        
        # 绘制
        screen.fill((0, 0, 0))  # 黑色背景
        player.draw(screen)
        player.draw_bullets(screen)
        player.draw_health_bar(screen, 10, 10)
        
        # 显示状态信息
        font = pg.font.Font(None, 36)
        
        # 生命值显示
        health_text = font.render(f"Health: {player.health_system.current_health}/{player.health_system.max_health}", True, (255, 255, 255))
        screen.blit(health_text, (10, 30))
        
        # 子弹数量显示
        bullet_text = font.render(f"Bullets: {len(player.bullets)}", True, (255, 255, 255))
        screen.blit(bullet_text, (10, 70))
        
        # 无敌状态显示
        invincible_text = font.render(f"Invincible: {player.invincible}", True, (255, 255, 255))
        screen.blit(invincible_text, (10, 110))
        
        # 控制说明
        controls_font = pg.font.Font(None, 24)
        controls_text = [
            "控制说明:",
            "WASD/方向键: 移动",
            "空格键: 射击", 
            "H键: 治疗(+20HP)",
            "T键: 受伤测试(-10HP)"
        ]
        
        for i, text in enumerate(controls_text):
            rendered_text = controls_font.render(text, True, (200, 200, 200))
            screen.blit(rendered_text, (10, 150 + i * 25))
        
        pg.display.flip()
        clock.tick(60)
    
    pg.quit()

if __name__ == "__main__":
    main()
