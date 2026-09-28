import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons
from mpl_toolkits.mplot3d import Axes3D


# 1. moutain defintion for option

def mountain_classic(x, y):
    # regular peak
    return 1200 * np.exp(-(x**2 + y**2) / 80000)

def mountain_ridge(x, y):
    # long ridge
    return 1200 * np.exp(-x**2 / 40000 - y**2 / 100000)

def mountain_twin_peaks(x, y):
    # two peaks
    peak1 = 1200 * np.exp(-(x**2 + y**2) / 70000)
    peak2 = 500 * np.exp(-((x - 80)**2 + (y - 50)**2) / 20000)
    return peak1 + peak2

# names
MOUNTAIN_OPTIONS = {
    "Classic Peak": mountain_classic,
    "Long Ridge": mountain_ridge,
    "Twin Peaks": mountain_twin_peaks
}

# current mountain selected
current_mountain_func = MOUNTAIN_OPTIONS["Classic Peak"]

# wrapper

def mountain_geometry(x, y):
    return current_mountain_func(x, y)


# 2.the calculus


def get_gradient(x, y):
    """
    Calculates the gradient vector
    points in the direction of steepest incline
    """
    h = 1.0
    dz_dx = (mountain_geometry(x + h, y) - mountain_geometry(x - h, y)) / (2 * h)
    dz_dy = (mountain_geometry(x, y + h) - mountain_geometry(x, y - h)) / (2 * h)
    return np.array([dz_dx, dz_dy])

def rotate_vector(vec, angle_degrees):
    """rotate by some angle"""
    theta = np.radians(angle_degrees)
    c, s = np.cos(theta), np.sin(theta)
    # rotation matrix math
    return np.array([vec[0]*c - vec[1]*s, vec[0]*s + vec[1]*c])


# 3. the path calculations

def calculate_ski_path(skill_val, speed_val):
    path = []

    # top position, but like a teeny bit off the side cause it doesn't move its on the direct top
    pos = np.array([0.1, 10.0])
    path.append([pos[0], pos[1], mountain_geometry(pos[0], pos[1])])

    # skill, range from 20ish to like 60 prolly
    max_safe_slope = 15 + (skill_val * 4.5)

    # Speed (1-10) for preffered slope angle
    target_slope = speed_val * 4.5

    # direction control
    # if we fall off the moutain, just look on either side
    trail_width = 120
    forced_side = 0 # 0 = Any, 1 = Force Right, -1 = Force Left

    # loop the thing until we get down
    for _ in range(2000):
        x, y = pos
        z = mountain_geometry(x, y)

        # Stop at bottom
        if z < 10: break

        # calculate gradient
        grad = get_gradient(x, y)
        grad_mag = np.linalg.norm(grad)

        if grad_mag == 0:
            # if flat just go fowrard a bit you known
            pos += np.array([0.5, 0.5])
            continue

        # fall line is opposite of gradient cause its going to be
        fall_line = -grad / grad_mag

        # what angles this sim will test, for speed purposes
        test_angles = [0, 30, -30, 60, -60, 85, -85]

        best_vec = None
        best_score = float('inf')

        # 3. check each angle
        for angle in test_angles:

            # make vector for direction
            candidate_dir = rotate_vector(fall_line, angle)

            # check boudnary
            # if at edge then turn
            if x > trail_width and angle < 0: continue # Don't go further right (negative angle relative to fall line might point right)
            # Simplified Logic: Check actual coordinate movement
            if (x > trail_width and candidate_dir[0] > 0): continue
            if (x < -trail_width and candidate_dir[0] < 0): continue

            # calc directional derivative
            # slope approx is dot product

            step_test = pos + (candidate_dir * 2.0)
            z_test = mountain_geometry(step_test[0], step_test[1])
            dz = z - z_test # heigh drop

            if dz <= 0: continue # ignore uphill

          #calculate slope angle
            slope_ratio = dz / 2.0
            slope_deg = np.degrees(np.arctan(slope_ratio))

            # selection part

            # Check skill to see if it is safe
            if slope_deg > max_safe_slope:
                continue

            # cost fucntion and see which one is the best for slope
            diff = abs(slope_deg - target_slope)

            if diff < best_score:
                best_score = diff
                best_vec = candidate_dir


        # actually move,no move = default flattest traversal
        if best_vec is None:

             best_vec = rotate_vector(fall_line, 85)

        pos = pos + (best_vec * 4.0) # Move 4 meters from positon before going again
        path.append([pos[0], pos[1], mountain_geometry(pos[0], pos[1])])

    return np.array(path)


# 3. visual


fig = plt.figure(figsize=(10, 8))
plt.subplots_adjust(bottom=0.25) # Make room for sliders
ax = fig.add_subplot(111, projection='3d')

def draw_plot(path_data):
    ax.clear()

    # moutain
    x = np.linspace(-200, 200, 50)
    y = np.linspace(-200, 200, 50)
    X, Y = np.meshgrid(x, y)
    Z = mountain_geometry(X, Y)
    ax.plot_surface(X, Y, Z, cmap='Blues', alpha=0.5, edgecolor='none')

    # path
    if len(path_data) > 0:
        # make path visible ontop of surface
        ax.plot(path_data[:,0], path_data[:,1], path_data[:,2] + 2, color='red', linewidth=3)

    ax.set_xlim(-200, 200)
    ax.set_ylim(-200, 200)
    ax.set_zlim(0, 1300)
    ax.set_title("Ski Route Optimizer")

def update(val):
    path = calculate_ski_path(slider_skill.val, slider_speed.val)
    draw_plot(path)
    fig.canvas.draw_idle()

# gui wigets

# 1. moutain selector things
# Located at Top-Left
ax_radio = plt.axes([0.05, 0.7, 0.15, 0.15], facecolor='#f0f0f0')
radio = RadioButtons(ax_radio, list(MOUNTAIN_OPTIONS.keys()))

def change_mountain(label):
    global current_mountain_func
    current_mountain_func = MOUNTAIN_OPTIONS[label]
    update(None)

radio.on_clicked(change_mountain)

# 2. sliders

ax_skill = plt.axes([0.2, 0.1, 0.6, 0.03])
ax_speed = plt.axes([0.2, 0.05, 0.6, 0.03])

slider_skill = Slider(ax_skill, 'Skill (1-10)', 1, 10, valinit=5, valstep=1)
slider_speed = Slider(ax_speed, 'Speed (1-10)', 1, 10, valinit=5, valstep=1)

slider_skill.on_changed(update)
slider_speed.on_changed(update)

# Initial Run
update(None)
plt.show()
