#!/usr/bin/python
#-*-coding:utf-8-*-
#
# SwarmToy v.0.2
# A frenetic game
# 7th of July 2007
# Alexander Rødseth
# rodseth@gmail.com
# GPL v.2 or later
#

try:
    import psyco
    psyco.full()
except ImportError:
    pass

import pygame
from pygame.locals import *
from random import choice
from math import sqrt

class Position:

    def __init__(self, pos):
        self.x, self.y = pos

    def pos(self):
        return self.x, self.y


class Energy:

    def __init__(self, amount):
        self.maxenergy = amount
        self.energy = amount

    def _energycheck(self):
        if self.energy < 0:
            self.energy = 0
        elif self.energy > self.maxenergy:
            self.energy = self.maxenergy


class Bound(Position):

    def __init__(self, pos, bounds):
        Position.__init__(self, pos)
        self.bounds = bounds
        self.left, self.top, self.width, self.height = bounds
        self.right = self.left + self.width
        self.bottom = self.top + self.height

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


class Food(Bound, Energy):
    """Represents a tiny lump of food"""

    def __init__(self, pos, bounds, energy=10):
        Bound.__init__(self, pos, bounds)
        Energy.__init__(self, energy)
        self.x += choice([-5, 5])
        self.y += choice([-5, 5])
        self._contain()
        self.randomcolor = choice([0, 50, 100])

    def color(self):
        i = self.energy / 10.0
        gray = int(i * 200.0)
        return (200 - gray, 200 - gray, int(i * 150.0) + self.randomcolor)


class Snack(Food):
    """Represents a different kind of food. It can move."""

    def __init__(self, pos, bounds):
        Food.__init__(self, pos, bounds, 180)
        self.ax = 1.0
        self.ay = 1.0
        self.gx = 0.0
        self.gy = 0.4

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


class LimitedIntelligence(Bound):
    """Adds some limited intelligence to a class with position and boundaries.
    Only meant to be inherited from.
    """

    def _closest(self, things):
        """Find the closest thing"""
        dist = int(sqrt((self.x - things[0].x) ** 2 + (self.y - things[0].y) ** 2))
        closest = things[0]
        for thing in things:
            d = int(sqrt((self.x - thing.x) ** 2 + (self.y - thing.y) ** 2))
            if d < dist:
                dist = d
                closest = thing
        return closest

    def _closest_to(self, things, pos):
        """Find the closest thing to a given position"""
        x = pos[0]
        y = pos[1]
        dist = int(sqrt((x - things[0].x) ** 2 + (y - things[0].y) ** 2))
        closest = things[0]
        for thing in things:
            d = int(sqrt((x - thing.x) ** 2 + (y - thing.y) ** 2))
            if d < dist:
                dist = d
                closest = thing
        return closest

    def _weakest(self, things):
        """Find the weakest thing"""
        minenergy = things[0].energy
        weakest = things[0]
        for thing in things:
            if thing.energy <= minenergy:
                weakest = thing
                minenergy = thing.energy
        return weakest

    def _strongest(self, things):
        """Find the strongest thing"""
        mostenergy = things[0].energy
        strongest = things[0]
        for thing in things:
            if thing.energy > mostenergy:
                strongest = thing
                mostenergy = thing.energy
        return strongest

    def _averagepos(self, things):
        """Find the average thing position"""
        x = 0
        y = 0
        for thing in things:
            x += thing.x
            y += thing.y
        x /= float(len(things))
        y /= float(len(things))
        return x, y

    def _towards(self, thing, speed=1):
        """Move directly towards a thing"""
        if self.x < thing.x:
            self.x += speed
        elif self.x > thing.x:
            self.x -= speed
        if self.y < thing.y:
            self.y += speed
        elif self.y > thing.y:
            self.y -= speed

    def _escape(self, thing, speed=3):
        """Move away from a thing"""
        # if the thing is on the left side, go to the right
        if (thing.x - self.left) < (self.right - thing.x):
            self.x += speed
        # if the thing is on the right side, go to the left
        elif (thing.x - self.left) > (self.right - thing.x):
            self.x -= speed
        # if the thing is on the top side, go to the bottom
        if (thing.y - self.top) < (self.bottom - thing.y):
            self.y += speed
        # if the thing is on the right side, go to the left
        elif (thing.y - self.top) > (self.bottom - thing.y):
            self.y -= speed

    def _anticorner(self, speed=1):
        """Keep to the center"""
        centerx = (self.right - self.left) / 2.0
        centery = (self.bottom - self.top) / 2.0
        dist = sqrt((self.x - centerx) ** 2 + (self.y - centery) ** 2)
        speed = max(speed, int(dist * 0.01))
        if self.x > centerx:
            self.x -= speed
        elif self.x < centerx:
            self.x += speed
        if self.y > centery:
            self.y -= speed
        elif self.y < centery:
            self.y += speed


class Bee(Bound, Energy, LimitedIntelligence):
    """Represents a little bee. It can move, eat, fight, die and have children."""

    randommove = 3
    strongescape = 0.6
    weakening = 0.3
    seekweak = 0.8
    seekcursor = 2.7
    escapecorner = 0.7
    lowenergy_seekaverage = 1.1
    mediumenergy_escapeaverage = 5.2
    okenergy_seekaverage = 0.4
    goodenergy_escapeaverage = 1.4
    seekfood = 5.8
    seeksnack = 8.2
    seeksnackhungry = 14.2
    seekaveragefood = 1.5
    seekaveragefoodthresh = 20
    childcostincrease = 15
    maxspeed = 8
    oldmoveinfluence = 0.25

    def __init__(self, pos, bounds):
        Bound.__init__(self, pos, bounds)
        Energy.__init__(self, 255)
        self.foodcount = 0
        self.childcost = 1


    def _met(self, thing):
        # This is what happens when a Bee meets a thing
        if self == thing:
            return
        if isinstance(thing, Bee):
            bee = thing
            if bee.energy == self.energy:
                # Two equally strong bees meet and fight just a bit
                bee.energy -= choice([0, 1, 2])
                self.energy -= choice([0, 1, 2])
            elif bee.energy < self.energy:
                # Kick the other bee
                diff = self.energy - bee.energy
                bee.energy -= int(diff * 0.2)
                bee.energy -= 1
            if (bee.foodcount == self.foodcount) and (abs(bee.energy - self.energy) < 30):
                # If they have eaten the same amount of food, make children and transfer the foodcount
                child = Bee((self.x, self.y)[:], self.bounds[:])
                child.foodcount = self.foodcount
                self.energy -= self.childcost
                return child
        elif isinstance(thing, Food):
            f = thing
            amount = int(f.energy * 0.2) + 1
            self.energy += amount
            f.energy -= amount
            self.foodcount += 1
        elif isinstance(thing, Snack):
            sna = thing
            self.energy += f.energy
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
        self._energycheck()
        children = self._see(bees)
        self._see(food)
        self._see(snack)
        self.x += choice(range(-Bee.randommove, Bee.randommove + 1))
        self.y += choice(range(-Bee.randommove, Bee.randommove + 1))
        weakest = self._weakest(bees)
        strongest = self._strongest(bees)
        if self == weakest:
            self._escape(strongest, Bee.strongescape)
            self.energy -= Bee.weakening
        else:
            self._towards(weakest, Bee.seekweak)
        if self.energy < 30:
            self._towards(Position(self._averagepos(bees)), Bee.lowenergy_seekaverage)
        elif self.energy < 150:
            self._escape(Position(self._averagepos(bees)), Bee.mediumenergy_escapeaverage)
        elif self.energy < 225:
            self._towards(Position(self._averagepos(bees)), Bee.okenergy_seekaverage)
        else:
            self._escape(Position(self._averagepos(bees)), Bee.goodenergy_escapeaverage)
        if snack:
            if self.energy < 100:
                self._towards(self._closest(snack), Bee.seeksnackhungry)
            else:
                self._towards(self._closest(snack), Bee.seeksnack)
        else:
            self._anticorner(Bee.escapecorner)
            self._towards(Position(cursorpos), Bee.seekcursor)
            if food:
                self._towards(self._closest(food), Bee.seekfood)
                if len(food) > Bee.seekaveragefoodthresh:
                    self._towards(Position(self._averagepos(food)), Bee.seekaveragefood)
            else:
                self.childcost += Bee.childcostincrease
        self._acelleration(Bee.maxspeed)
        self._contain()
        return children

    def color(self):
        # Energy can be changed by other bees, that's why the check is here
        self._energycheck()
        return (255 - self.energy, self.energy, 0)


class World:

    circlesize = 4

    def __init__(self, surface, numbees=40, numfood=40):
        self.surface = surface
        size = surface.get_size()
        self.bounds = (0, 0, size[0], size[1])
        # Initialize the bees
        self.bees = []
        for i in range(numbees):
            x = choice(range(size[0] / 8))
            y = choice(range(size[1] / 8))
            self.bees.append(Bee((x, y), self.bounds))
        # Initalize some food
        self.food = []
        for i in range(numfood):
            x = choice(range(size[0]))
            y = choice(range(size[1]))
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
            if bee.energy < 10:
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


class Game:

    def __init__(self, size):
        pygame.display.init()
        self.screen = pygame.display.set_mode(size)
        pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN])
        pygame.mouse.set_visible(False)

    def mainloop(self):
        world = World(self.screen)
        size = self.screen.get_size()
        clock = pygame.time.Clock()

        BGCOLOR = (0, 0, 0)
        LINECOLOR = (128, 128, 128)
        x = y = 150

        right = size[0] - 1
        bottom = size[1] - 1

        # Blank out the screen first
        self.screen.fill(BGCOLOR)
        pygame.display.flip()

        running = True
        pause = False
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
                        world = World(self.screen)
                    elif event.key == pygame.K_RETURN:
                        world = World(self.screen, 0, 0)
                    elif event.key == pygame.K_p:
                        pause = not pause
                        if pause:
                            pygame.mouse.set_visible(True)
                        else:
                            pygame.mouse.set_visible(False)
                    elif event.key == pygame.K_f:
                        pygame.display.toggle_fullscreen()
                elif event.type == pygame.QUIT:
                    running = False

            if not pause:
                rects = []
                self.screen.fill(BGCOLOR)
                rects += world.draw((x, y))
                rects.append(pygame.draw.line(self.screen, LINECOLOR, (x - 8, y), (x + 9, y), 2))
                rects.append(pygame.draw.line(self.screen, LINECOLOR, (x, y - 8), (x, y + 9), 2))

                #pygame.display.update(rects)
                pygame.display.flip()

            pygame.event.pump()
            clock.tick(24)

        pygame.display.quit()

def main():
    game = Game((640, 480))
    game.mainloop()

if __name__ == "__main__":
    main()
