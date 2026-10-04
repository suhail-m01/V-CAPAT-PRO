"""Optional pre-trained SB3 controller adapter; model weights are not shipped."""
from pathlib import Path

class PretrainedRLController:
    def __init__(self,model_path):
        if not Path(model_path).is_file():raise FileNotFoundError('No pre-trained policy supplied. Train and provide an SB3 model .zip.')
        try:from stable_baselines3 import PPO
        except ImportError as exc:raise RuntimeError('Install stable-baselines3 to use a supplied RL policy') from exc
        self.policy=PPO.load(str(model_path))
    def command(self,observation):
        action,_=self.policy.predict(observation,deterministic=True)
        return tuple(float(v) for v in action)
