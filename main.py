#!/usr/bin/python
#-*-coding:utf-8-*-
#
# SwarmToy v.0.1
# 7th of July 2007
# Alexander Rødseth
# rodseth@gmail.com
# GPL v.2 or later
#

try:
    import psyco
    psyco.full()
except ImportException:
    pass

import pygame
from pygame.locals import *
import random
import math

class BeeWrap:

    def __init__(self, pos):
        self.x, self.y = pos

class Food:

    def __init__(self, pos, bounds):
        self.x, self.y = pos
        self.energy = 10

    def color(self):
        return (0, 0, int(self.energy * 25.5))

    def pos(self):
        return self.x, self.y

class Snack(Food):

    def __init__(self, pos, bounds):
        self.x, self.y = pos
        self.bounds = bounds
        self.left, self.top, self.width, self.height = bounds
        self.right = self.left + self.width
        self.bottom = self.top + self.height
        self.ax = 1.0
        self.ay = 1.0
        self.gx = 0.0
        self.gy = 0.4
        self.energy = 180

    def _contain(self):
        if self.x >= self.width:
            self.x = self.width - 1
        if self.y >= self.height:
            self.y = self.height - 1
        if self.x < self.left:
            self.x = self.left
        if self.y < self.top:
            self.y = self.top
        self.x = int(self.x)
        self.y = int(self.y)

    def _bounce(self):
        if self.x >= self.right:
            self.ax *= -0.8
        elif self.x < self.left:
            self.ax *= -0.8
        if self.y >= self.bottom:
            self.ay *= -0.5
            self.energy *= 0.9
            self.energy -= 1
        elif self.y < self.top:
            self.ay *= -0.8
            self.energy *= 0.9
            self.energy -= 1
        if (abs(self.y - self.bottom) < 5) and (abs(self.ay) < 1):
            self.gy *= -1.0
            self.ax *= -1.0
        elif (abs(self.y - self.top) < 5) and (abs(self.ay) < 1):
            self.gy *= -1.0
            self.ax *= -1.0

    def move(self):
        self.ax += self.gx
        self.ay += self.gy
        self.x += self.ax
        self.y += self.ay
        self._bounce()
        self._contain()
        if self.energy < 10:
            self.energy = 0

    def color(self):
        i = self.energy / 180.0
        r = 255.0 * i
        g = 50.0 + 200.0 * max(0, (i - 0.8)) * 5.0
        b = 20.0 + 230.0 * i
        return (int(r), int(g), int(b))

class Bee:

    randommove = 3
    strongescape = 0.6
    weakening = 0.3
    seekweak = 0.8
    seekcursor = 2.7
    escapecorner = 0.7
    lowhealth_seekaverage = 1.1
    mediumhealth_escapeaverage = 5.2
    okhealth_seekaverage = 0.4
    goodhealth_escapeaverage = 1.4
    seekfood = 5.8
    seeksnack = 8.2
    seeksnackhungry = 14.2
    seekaveragefood = 1.5
    seekaveragefoodthresh = 20
    childcostincrease = 15
    maxspeed = 8
    oldmoveinfluence = 0.25

    def __init__(self, pos, bounds):
        self.x, self.y = pos
        self.bounds = bounds
        self.left, self.top, self.width, self.height = bounds
        self.right = self.left + self.width
        self.bottom = self.top + self.height
        self.health = 255
        self.foodcount = 0
        self.childcost = 1

    def _contain(self):
        if self.x >= self.width:
            self.x = self.width - 1
        if self.y >= self.height:
            self.y = self.height - 1
        if self.x < self.left:
            self.x = self.left
        if self.y < self.top:
            self.y = self.top
        self.x = int(self.x)
        self.y = int(self.y)

    def _closest(self, bees):
        # Find the closest bee or food
        dist = int(math.sqrt((self.x - bees[0].x) ** 2 + (self.y - bees[0].y) ** 2))
        closest = bees[0]
        for bee in bees:
            d = int(math.sqrt((self.x - bee.x) ** 2 + (self.y - bee.y) ** 2))
            if d < dist:
                dist = d
                closest = bee
        return closest

    def _closest_to(self, bees, pos):
        x = pos[0]
        y = pos[1]
        # Find the closest bee or food to a position
        dist = int(math.sqrt((x - bees[0].x) ** 2 + (y - bees[0].y) ** 2))
        closest = bees[0]
        for bee in bees:
            d = int(math.sqrt((x - bee.x) ** 2 + (y - bee.y) ** 2))
            if d < dist:
                dist = d
                closest = bee
        return closest

    def _weakest(self, bees):
        # Find the weakest bee
        minhealth = bees[0].health
        weakest = bees[0]
        for bee in bees:
            if bee.health <= minhealth:
                weakest = bee
                minhealth = bee.health
        return weakest

    def _strongest(self, bees):
        # Find the strongest bee
        maxhealth = bees[0].health
        strongest = bees[0]
        for bee in bees:
            if bee.health > maxhealth:
                strongest = bee
                maxhealth = bee.health
        return strongest

    def _averagepos(self, bees):
        # Find the average bee position
        x = 0
        y = 0
        for bee in bees:
            x += bee.x
            y += bee.y
        x /= float(len(bees))
        y /= float(len(bees))
        return x, y

    def _towards(self, bee, speed=1):
        if self.x < bee.x:
            self.x += speed
        elif self.x > bee.x:
            self.x -= speed
        if self.y < bee.y:
            self.y += speed
        elif self.y > bee.y:
            self.y -= speed

    def _escape(self, bee, speed=3):
        # if the bee is on the left side, go to the right
        if (bee.x - self.left) < (self.right - bee.x):
            self.x += speed
        # if the bee is on the right side, go to the left
        elif (bee.x - self.left) > (self.right - bee.x):
            self.x -= speed
        # if the bee is on the top side, go to the bottom
        if (bee.y - self.top) < (self.bottom - bee.y):
            self.y += speed
        # if the bee is on the right side, go to the left
        elif (bee.y - self.top) > (self.bottom - bee.y):
            self.y -= speed

    def _anticorner(self, speed=1):
        centerx = (self.right - self.left) / 2.0
        centery = (self.bottom - self.top) / 2.0
        dist = math.sqrt((self.x - centerx) ** 2 + (self.y - centery) ** 2)
        speed = max(speed, int(dist * 0.01))
        if self.x > centerx:
            self.x -= speed
        elif self.x < centerx:
            self.x += speed
        if self.y > centery:
            self.y -= speed
        elif self.y < centery:
            self.y += speed

    def _met(self, thing):
        # This is what happens when a Bee meets a thing
        if self == thing:
            return
        if isinstance(thing, Bee):
            bee = thing
            if bee.health == self.health:
                # Two equally strong bees meet and fight just a bit
                bee.health -= random.choice([0, 1, 2])
                self.health -= random.choice([0, 1, 2])
            elif bee.health < self.health:
                # Kick the other bee
                diff = self.health - bee.health
                bee.health -= int(diff * 0.2)
                bee.health -= 1
            if (bee.foodcount == self.foodcount) and (abs(bee.health - self.health) < 30):
                # If they have eaten the same amount of food, make children and transfer the foodcount
                child = Bee((self.x, self.y)[:], self.bounds[:])
                child.foodcount = self.foodcount
                self.health -= self.childcost
                return child
        elif isinstance(thing, Food):
            f = thing
            amount = int(f.energy * 0.2) + 1
            self.health += amount
            f.energy -= amount
            self.foodcount += 1
        elif isinstance(thing, Snack):
            sna = thing
            self.health += f.energy
            f.energy = 0
            self.foodcount += 1
        return None

    def _see(self, bees, margin=3):
        xs = range(self.x - margin, self.x + margin)
        ys = range(self.y - margin, self.y + margin)
        # Seeing other bees can produce children
        children = []
        for bee in bees:
            if (bee.x in xs) and (bee.y in ys):
                children.append(self._met(bee))
        return [child for child in children if child != None]

    def _healthcheck(self):
        if self.health < 0:
            self.health = 0
        elif self.health > 255:
            self.health = 255

    def _acelleration(self, maxspeed):
        # Convert the movement into acelleration instead, and cap at maxspeed
        # self.ox and self.oy is the original position
        diffx = self.x - self.ox
        diffy = self.y - self.oy
        if diffx > maxspeed:
            diffx = maxspeed
        elif diffx < -maxspeed:
            diffx = -maxspeed
        if diffy > maxspeed:
            diffy = maxspeed
        elif diffy < -maxspeed:
            diffy = -maxspeed
        self.x = ((self.ox + diffx) * (1.0 - Bee.oldmoveinfluence) + self.ox * Bee.oldmoveinfluence)
        self.y = ((self.oy + diffy) * (1.0 - Bee.oldmoveinfluence) + self.oy * Bee.oldmoveinfluence)

    def move(self, bees, food, snack, cursorpos):
        self.ox = self.x
        self.oy = self.y
        self._healthcheck()
        children = self._see(bees)
        self._see(food)
        self._see(snack)
        self.x += random.choice(range(-Bee.randommove, Bee.randommove + 1))
        self.y += random.choice(range(-Bee.randommove, Bee.randommove + 1))
        weakest = self._weakest(bees)
        strongest = self._strongest(bees)
        if self == weakest:
            self._escape(strongest, Bee.strongescape)
            self.health -= Bee.weakening
        else:
            self._towards(weakest, Bee.seekweak)
        if self.health < 30:
            self._towards(BeeWrap(self._averagepos(bees)), Bee.lowhealth_seekaverage)
        elif self.health < 150:
            self._escape(BeeWrap(self._averagepos(bees)), Bee.mediumhealth_escapeaverage)
        elif self.health < 225:
            self._towards(BeeWrap(self._averagepos(bees)), Bee.okhealth_seekaverage)
        else:
            self._escape(BeeWrap(self._averagepos(bees)), Bee.goodhealth_escapeaverage)
        if snack:
            if self.health < 100:
                self._towards(self._closest(snack), Bee.seeksnackhungry)
            else:
                self._towards(self._closest(snack), Bee.seeksnack)
        else:
            self._anticorner(Bee.escapecorner)
            self._towards(BeeWrap(cursorpos), Bee.seekcursor)
            if food:
                self._towards(self._closest(food), Bee.seekfood)
                if len(food) > Bee.seekaveragefoodthresh:
                    self._towards(BeeWrap(self._averagepos(food)), Bee.seekaveragefood)
            else:
                self.childcost += Bee.childcostincrease
        self._acelleration(Bee.maxspeed)
        self._contain()
        return children

    def pos(self):
        return self.x, self.y

    def color(self):
        self._healthcheck()
        return (255 - self.health, self.health, 0)

class World:

    circlesize = 4

    def __init__(self, surface, numbees=40, numfood=40):
        self.surface = surface
        size = surface.get_size()
        self.bounds = (0, 0, size[0], size[1])
        # Initialize the bees
        self.bees = []
        for i in range(numbees):
            x = random.choice(range(size[0] / 8))
            y = random.choice(range(size[1] / 8))
            self.bees.append(Bee((x, y), self.bounds))
        # Initalize some food
        self.food = []
        for i in range(numfood):
            x = random.choice(range(size[0]))
            y = random.choice(range(size[1]))
            self.food.append(Food((x, y), (0, 0, size[0], size[1])))
        self.circleradius = World.circlesize
        # No snack yet
        self.snack = []

    def addbee(self, cursorpos):
        self.bees.append(Bee(cursorpos, self.bounds))

    def addfood(self, cursorpos):
        self.food.append(Food(cursorpos, self.bounds))

    def addsnack(self, cursorpos):
        self.snack.append(Snack(cursorpos, self.bounds))

    def draw(self, cursorpos):
        kill = []
        create = []
        rects = []
        for bee in self.bees:
            children = bee.move(self.bees, self.food, self.snack, cursorpos)
            if children:
                create += children
            if bee.health < 10:
                kill.append(bee)
                continue
            rects.append(pygame.draw.circle(self.surface, bee.color(), bee.pos(), self.circleradius))
        for bee in kill:
            self.bees.remove(bee)
        if (len(self.bees) < 20) and create:
            for bee in create[:20]:
                self.bees.append(bee)
        kill = []
        for f in self.food:
            if f.energy < 5:
                kill.append(f)
                continue
            rects.append(pygame.draw.circle(self.surface, f.color(), f.pos(), self.circleradius))
        for f in kill:
            self.food.remove(f)
        kill = []
        for sna in self.snack:
            sna.move()
            if sna.energy < 5:
                kill.append(sna)
                continue
            rects.append(pygame.draw.circle(self.surface, sna.color(), sna.pos(), self.circleradius))
        for sna in kill:
            self.snack.remove(sna)
        return rects


def init(size):
    pygame.display.init()
    screen = pygame.display.set_mode(size)
    pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN])
    pygame.mouse.set_visible(False)
    return screen

def mainloop(screen):
    world = World(screen)
    size = screen.get_size()
    clock = pygame.time.Clock()

    BGCOLOR = (0, 0, 0)
    LINECOLOR = (128, 128, 128)
    x = y = 150

    right = size[0] - 1
    bottom = size[1] - 1

    # Blank out the screen... in yellow!?
    screen.fill(BGCOLOR)
    pygame.display.flip()

    running = True
    while running:

        events = pygame.event.get()
        if events:
            event = events[-1]
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if event.button == 1:
                    world.addfood(event.pos)
                elif event.button == 3:
                    world.addbee(event.pos)
                elif event.button == 2:
                    world.addsnack(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                if event.buttons[0]:
                    world.addfood(event.pos)
                elif event.buttons[2]:
                    world.addbee(event.pos)
                elif event.buttons[1]:
                    world.addsnack(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                    running = False
                elif event.key == pygame.K_SPACE:
                    world = World(screen)
                elif event.key == pygame.K_RETURN:
                    world = World(screen, 0, 0)
            elif event.type == pygame.QUIT:
                running = False

        screen.fill(BGCOLOR)

        rects = []
        rects += world.draw((x, y))
        rects.append(pygame.draw.line(screen, LINECOLOR, (x - 9, y), (x + 10, y), 2))
        rects.append(pygame.draw.line(screen, LINECOLOR, (x, y - 9), (x, y + 10), 2))
        
        #pygame.display.update(rects)
        pygame.display.flip()

        pygame.event.pump()
        clock.tick(30)

    pygame.display.quit()

def main():
    screen = init((640, 480))
    mainloop(screen)

if __name__ == "__main__":
    main()
