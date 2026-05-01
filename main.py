import sys
from time import sleep
import pygame
from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien


class AlienInvasion:
  """管理游戏资源和行为的类"""
  def __init__(self):
    """初始化游戏并创建游戏资源"""
    pygame.init()

    self.clock = pygame.time.Clock()
    self.settings = Settings()

    self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
    # self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption('外星人入侵')

    # 创建一个用于存储游戏统计信息的实例，并创建记分牌
    self.stats = GameStats(self)
    self.sb = Scoreboard(self)

    # 飞船实例
    self.ship = Ship(self)

    # 子弹分组
    self.bullets = pygame.sprite.Group()

    # 外星人
    self.aliens = pygame.sprite.Group()
    self._create_fleet()

    # 游戏启动后处于活动状态
    self.game_active = False

    # 创建开始按钮
    self.play_button = Button(self, "Play")

  def _fire_bullet(self):
    """创建一颗子弹，并将其加入到编组bullets中"""
    if len(self.bullets) < self.settings.bullet_allowed:
      new_bullet = Bullet(self)
      self.bullets.add(new_bullet)

  def _create_alien(self, postion_x, postion_y):
    """创建一个外星人并将其加入舰队"""
    new_alien = Alien(self)
    new_alien.x = postion_x
    new_alien.rect.x = postion_x
    new_alien.rect.y = postion_y
    self.aliens.add(new_alien)

  def _create_fleet(self):
    """创建外星人舰队"""
    # 创建一个外星人，再不断添加，直到没有空间添加外星人为止
    # 外星人的间距为外星人的宽度
    alien = Alien(self)
    alien_width, alien_height = alien.rect.size
    current_x, current_y = alien_width, alien_height
    # 飞船之间的间距
    distance_x = 2 * alien_width
    distance_y = 3 * alien_height

    while current_y < (self.settings.screen_height - distance_y):
      while current_x < (self.settings.screen_width - distance_x):
        self._create_alien(current_x, current_y)
        current_x += distance_x
      # 添加一行外星人后，重置x值并递增y值
      current_x = alien_width
      current_y += 2 * alien_height

  def _ship_hit(self):
    """响应飞船被外星人撞到"""
    if self.stats.ship_left > 0:
      # 将ship_left减1
      self.stats.ship_left -= 1
      self.sb.prep_ships()

      # 清空外星人列表和子弹列表
      self.bullets.empty()
      self.aliens.empty()

      # 创建一个新舰队，并将飞船放在屏幕底部的中央
      self._create_fleet()
      self.ship.center_ship()

      # 暂停
      sleep(0.5)
    else:
      # 飞船limit耗尽，游戏结束
      self.game_active = False
      pygame.mouse.set_visible(True)

  def _check_keydown_events(self, event):
    """响应按键"""
    if not self.game_active:
      return

    if event.key == pygame.K_RIGHT:
      self.ship.moving_right = True
    elif event.key == pygame.K_LEFT:
      self.ship.moving_left = True
    elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
      sys.exit()
    elif event.key == pygame.K_SPACE:
      # 按空格键开火
      self._fire_bullet()

  def _check_keyup_events(self, event):
    """响应松开"""
    if event.key == pygame.K_RIGHT:
      self.ship.moving_right = False
    elif event.key == pygame.K_LEFT:
      self.ship.moving_left = False

  def _check_events(self):
    # 侦听键盘和鼠标事件
    for event in pygame.event.get():
      event_type = event.type
      if event_type == pygame.QUIT:
        sys.exit()

      elif event_type == pygame.KEYDOWN:
        self._check_keydown_events(event)

      elif event_type == pygame.KEYUP:
        self._check_keyup_events(event)

      elif event_type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = pygame.mouse.get_pos()
        self._check_play_button(mouse_pos)

  def _change_fleet_direction(self):
    """将舰队向下移动，并改变舰队的移动方向"""
    for alien in self.aliens.sprites():
      alien.rect.y += self.settings.fleet_drop_speed
    self.settings.fleet_direction *= -1

  def _check_fleet_edges(self):
    """有外星人到达边缘时采取相应的措施"""
    for alien in self.aliens.sprites():
      if alien.check_edges():
        self._change_fleet_direction()
        break

  def _check_aliens_bottom(self):
    """检查是否有外星人到达屏幕底端"""
    for alien in self.aliens.sprites():
      if (alien.rect.bottom >= self.settings.screen_height):
        # 像飞船被撞到一样进行处理
        self._ship_hit()
        break

  def _check_play_button(self, mouse_pos):
    """在玩家单击Play按钮时开始新游戏"""
    button_clicked = self.play_button.rect.collidepoint(mouse_pos)
    if button_clicked and not self.game_active:
      # 还原游戏设置
      self.settings.initialize_dynamic_settings()

      # 重置游戏的统计信息
      self.stats.reset_stats()
      self.sb.prep_score()
      self.sb.prep_level()
      self.sb.prep_ships()
      self.game_active = True

      # 清空外星人列表和子弹列表
      self.aliens.empty()
      self.bullets.empty()

      # 创建一群新的外星人并让飞船居中
      self._create_fleet()
      self.ship.center_ship()

      # 隐藏光标
      pygame.mouse.set_visible(False)

  def _update_screen(self):
    # 每次循环时都重绘屏幕
    self.screen.fill(self.settings.bg_color);

    if self.game_active:
      # 绘制子弹
      for bullet in self.bullets.sprites():
        bullet.draw_bullet()

      # 绘制飞船
      self.ship.blitme()

      # 绘制外星舰队
      self.aliens.draw(self.screen)

      # 显示得分
      self.sb.show_score()

    # 如果游戏处于非活动状态时，绘制开始按钮
    if not self.game_active:
      self.play_button.draw_button()

    # 让最近回执的屏幕可见
    pygame.display.flip()

  def _check_bullet_alien_collisions(self):
    """响应子弹和外星人的碰撞"""
    # 删除发生碰撞的子弹和外星人
    collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

    if collisions:
      for aliens in collisions.values():
        self.stats.score += self.settings.alien_pints * len(aliens)
      self.sb.prep_score()
      self.sb.check_high_score()

    if not self.aliens:
      # 删除现有的子弹并创建新的舰队
      self.bullets.empty()
      self._create_fleet()
      self.settings.increase_speed()

      # 提高等级
      self.stats.level += 1
      self.sb.prep_level()

  def _update_bullets(self):
    """更新子弹的位置，并删除已消失的子弹"""
    self.bullets.update()
    # 删除已消失的子弹
    # 遍历时需要保持一个不变的副本
    for bullet in self.bullets.copy():
      if bullet.rect.bottom <= 0:
        self.bullets.remove(bullet)
    self._check_bullet_alien_collisions()

  def _update_aliens(self):
    """检查舰队边缘，并更新舰队中所有外星人的位置"""
    self._check_fleet_edges()
    self.aliens.update()

    # 检查外星人和飞船之间的碰撞
    if pygame.sprite.spritecollideany(self.ship, self.aliens):
      self._ship_hit()

    # 检查是否有外星人到达屏幕底端
    self._check_aliens_bottom()

  def run_ganme(self):
    """开始游戏的主循环"""
    while True:
      self._check_events()

      if self.game_active:
        self.ship.update()
        self._update_bullets()
        self._update_aliens()

      self._update_screen()
      self.clock.tick(60);

if __name__ == '__main__':
  # 创建游戏实例并运行游戏
  ai = AlienInvasion()
  ai.run_ganme()
