#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Calipsomulator - a simple CA and Agent-based simulator
# 2026, nb@su
# 
# GUI: curseur, z, shift+z, d, shift+d, reset, shift-reset
#

import random
import csv
import pygame
import numpy as np

try:
    from numba import njit
except ImportError:
    print ("[WARNING] Numba not available.")
    def njit(*args, **kwargs):
        def wrapper(f):
            return f
        return wrapper

import calipsolib
from calipsolib import Agent

# =-=-= simulation parameters

params = {
    "iteration" : 0,
    "nb_infected" : 0,
    "sane_count" : 0,
    "infected_count" : 0,
    "recover_count" : 0,
    "P_reproduction" : 0.05,
    "P_sanesick" : 0.001,
    "max_life" : 150,
    "recover" : 100,
    "iteration_counted" : False
}

# =-=-= Defining cell types

EMPTY = 0

colors_ca = {
    EMPTY: (255, 255, 255),
}

# =-=-= Defining agent types

SANE = 0
INFECTED = 1
RECOVER = 2

colors_agents = {
    SANE : (0, 200, 0),
    INFECTED : (200, 0, 0),
    RECOVER : (100, 100, 0),
}

# Files creation

file = open("./TME03/SANE_Count.csv", "w")
file.close()

file = open("./TME03/INFECTED_Count.csv", "w")
file.close()

file = open("./TME03/RECOVER_Count.csv", "w")
file.close()

# =-=-= user-defined agents

class Person(Agent):
    def __init__(self, x, y, params) :
        super().__init__(x, y, "Person", params)
        self.type = SANE
        self.running = True
        self.age = 0
        
    def move(self, grid, agents) :
        dx, dy = grid.shape

        if params["iteration_counted"] == False :
            params["sane_count"] = sum(1 for a in agents if a.type == SANE)
            params["infected_count"] = sum(1 for a in agents if a.type == INFECTED)
            params["recover_count"] = sum(1 for a in agents if a.type == RECOVER)
            params["iteration_counted"] = True

        # Infected first production
        if params["nb_infected"] <= 10 :
            self.type = INFECTED
            self.age = 0
            params["nb_infected"] += 1
        
        # Slow down the movement of the infected
        if self.type == INFECTED and random.random() < 0.5 :
            return

        # Moving randomly
        delta_x, delta_y = random.choice([(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)])
        self.x = (self.x + delta_x) % self.dx
        self.y = (self.y + delta_y) % self.dy

        # Sane production with a probability : 'P_reproduction'
        if random.random() < params["P_reproduction"] and grid[self.x, self.y] == EMPTY :
            for a in agents :
                if a.type == SANE and a.running == False and (a.x == self.x and a.y == self.y) :
                    a.running = True
                    a.age = 0
                    self.running = True
                    self.age = 0

        # Sane avoid infected persons
        if self.running :
            if self.type == SANE :
                if grid[(self.x + 1)%dx, self.y] == INFECTED :
                    self.x = (self.x - 1)%dx
            
                elif grid[(self.x - 1)%dx, self.y] == INFECTED :
                    self.x = (self.x + 1)%dx
                    
                elif grid[self.x, (self.y + 1)%dy] == INFECTED :
                    self.y = (self.y - 1)%dy

                elif grid[self.x, (self.y - 1)%dy] == INFECTED :
                    self.y = (self.y + 1)%dy
        
        # Sane got infected
        for a in agents :
            if self.type == SANE and a.type == INFECTED and a.x == self.x and a.y == self.y :
                self.type = INFECTED

        # Infected got recovered after 'recover' days
        if self.type == INFECTED and self.age > params["recover"] :
            self.type = RECOVER

        # Sane got infected with a probability : 'P_sanesick'
        if self.type == SANE and random.random() < params["P_sanesick"] :
            self.type = INFECTED

        self.age += 1

        # Person is dead after 'max_life' days
        if self.age > params["max_life"] :
            self.running = False
            grid[self.x, self.y] = EMPTY
            return
        
# Persons creation
def make_agents(params):
    dx = params["dx"]
    dy = params["dy"]
    retValue = []

    for i in range (500):
        retValue.append(Person(x = random.randint(0, dx-1), y = random.randint(0, dy-1), params = params))

    return retValue

# =-=-= user-defined cellular automata

def init_simulation(params):
    dx = params["dx"]
    dy = params["dy"]

    grid = np.zeros((dx, dy), dtype=np.uint8)
    newgrid = np.empty((dx, dy), dtype=np.uint8)

    return grid, newgrid

# @njit(cache=True)
def ca_step(grid, newgrid):
    global params

    # Show population of agents
    pygame.display.set_caption(f"Sane : {params['sane_count']} | Infected : {params['infected_count']} | Recover : {params['recover_count']}")

    params["iteration_counted"] = False

    dx, dy = grid.shape

    for x in range (dx):
        for y in range (dy):
            newgrid[x, y] = grid[x, y]
    
    # Files updating
    with open("./TME03/SANE_Count.csv", "a", newline="") as file :
        writer = csv.writer(file)
        writer.writerow([params["iteration"], params["sane_count"]])

    with open("./TME03/INFECTED_Count.csv", "a", newline="") as file :
        writer = csv.writer(file)
        writer.writerow([params["iteration"], params["infected_count"]])

    with open("./TME03/RECOVER_Count.csv", "a", newline="") as file :
        writer = csv.writer(file)
        writer.writerow([params["iteration"], params["recover_count"]])

    params["iteration"] += 1
    
# =-=-= run

if __name__ == "__main__":
    calipsolib.run(
        params=params, # user-defined
        init_simulation=init_simulation, # user-defined
        ca_step=ca_step, # user-defined
        make_agents=make_agents, # user-defined
        colors_ca=colors_ca,
        colors_agents=colors_agents,
        dx=80, # CA width
        dy=80, # CA height
        display_dx=800,
        display_dy=800,
        title="Sane-Infected-Recover Model", 
        verbose=False, # display stuff (can be used by user)
        fps=10 # steps per seconds (default: 60)
    )
