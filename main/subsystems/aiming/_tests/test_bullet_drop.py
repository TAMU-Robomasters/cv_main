import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image

class Turret:
    def __init__(self, pitch):
        self.pitch = np.radians(pitch)
        
        self.bullet_speed = 27
        self.pivot_height = 1.5
        self.barrel_length = 0.22
        self.cam_disp = -0.034
        self.fov = 57
        
        # parameters implemented only for the image
        self.barrel_width = 0.07
        self.pivot_radius = 0.07

        self.traj_origin = (self.barrel_length * np.cos(self.pitch), 
                            self.pivot_height + self.barrel_length * np.sin(self.pitch))
        self.cam_origin = (self.traj_origin[0] - self.cam_disp * np.sin(self.pitch), 
                            self.traj_origin[1] + self.cam_disp * np.cos(self.pitch))
        
    def adjust_pitch(self, amount):
        self.pitch += amount
        self.traj_origin = (self.barrel_length * np.cos(self.pitch), 
                            self.pivot_height + self.barrel_length * np.sin(self.pitch))
        self.cam_origin = (self.traj_origin[0] - self.cam_disp * np.sin(self.pitch), 
                            self.traj_origin[1] + self.cam_disp * np.cos(self.pitch))

class Target:
    def __init__(self, turret, x, y):
        self.height = 0.125     # meters
        self.attitude = np.radians(75)      # degrees

        self.x = x
        self.y = y

        delta_x = x - turret.cam_origin[0]
        delta_y = y - turret.cam_origin[1]
        print(np.degrees(np.arctan2(delta_y, delta_x)))
        self.vert_angle = np.arctan2(delta_y, delta_x) - turret.pitch
        self.distance = np.cos(self.vert_angle) * (delta_x**2 + delta_y**2)**0.5
        
        # parameters implemented only for the image
        self.width = 0.03     # meters

def draw_environment(turret, target, filename):
    fig = plt.figure()

    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    ax.axes.set_aspect('equal')

    # draw turret
    barrel_corner_pivot = (turret.barrel_width / 2 * np.sin(turret.pitch), 
                    turret.pivot_height - (turret.barrel_width / 2 * np.cos(turret.pitch)))
    barrel = mpl.patches.Rectangle(barrel_corner_pivot,
                                    turret.barrel_length, 
                                    turret.barrel_width, 
                                    angle=np.degrees(turret.pitch), fc="b")
    pivot = mpl.patches.Circle((0, turret.pivot_height), turret.pivot_radius, fc="w", ec="b", lw=3)
    ax.add_patch(barrel)
    ax.add_patch(pivot)
    
    # draw trajectory
    delta_t = 1     # seconds
    time = np.linspace(0, 2, 100)
    x = turret.traj_origin[0] + turret.bullet_speed * np.cos(turret.pitch) * time
    y = turret.traj_origin[1] + turret.bullet_speed * np.sin(turret.pitch) * time + 0.5 * -9.81 * time**2
    ax.plot(x, y, "r--")

    # draw armor
    plate_corner_pivot = (target.x + -target.height / 2 * np.cos(target.attitude) + target.width * np.sin(target.attitude),
                            target.y + -target.height / 2 * np.sin(target.attitude) - target.width * np.cos(target.attitude))
    plate = mpl.patches.Rectangle(plate_corner_pivot,
                                    target.height,
                                    target.width,
                                    angle=np.degrees(target.attitude), fc="b")
    ax.add_patch(plate)

    # draw ground
    ax.axhline(0, c="k")

    # rescale axes
    ylim = [-0.1, turret.pivot_height + 2 * turret.pivot_radius]
    xlim = [-2 * turret.pivot_radius, target.x + 0.1]

    ax.set_ylim(ylim)
    ax.set_xlim(xlim)
    fig.savefig(filename)

""" returns change in pitch (in rad) """
def test(turret, target):
    return 0

if __name__ == "__main__":
    turret = Turret(-10)
    target = Target(turret, 3, 0.5)

    draw_environment(turret, target, "foo.jpg")
    turret.pitch += test(turret, target)
    # draw_environment(turret, target, "after.jpg")