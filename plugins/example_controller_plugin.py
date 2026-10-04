"""Example trusted alternative: bounded proportional pan/tilt controller."""
PLUGIN_KIND='controller'

class ExampleController:
    def step(self,error_x_deg,error_y_deg,dt,limit_deg_s):
        return (max(-limit_deg_s,min(limit_deg_s,8.*error_x_deg)),
                max(-limit_deg_s,min(limit_deg_s,8.*error_y_deg)))

PLUGIN_CLASS=ExampleController
