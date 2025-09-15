"""
TextWorld Environment Adapter for KGRL research framework.

Provides unified TextWorld environment interface with fallback to mock environment.
"""

import random
from typing import Dict, List, Any, Optional, Tuple

try:
    import textworld
    TEXTWORLD_AVAILABLE = True
except ImportError:
    TEXTWORLD_AVAILABLE = False

from .base_env import BaseEnvironment


class TextWorldAdapter(BaseEnvironment):
    """TextWorld environment adapter with mock fallback."""
    
    def __init__(self, config: Dict[str, Any] = None):
        env_id = config.get("env_id", "textworld_default") if config else "textworld_default"
        super().__init__(env_id, config)
        
        # TextWorld specific configuration
        self.nb_objects = self.config.get("nb_objects", 10)
        self.nb_rooms = self.config.get("nb_rooms", 5)
        self.quest_length = self.config.get("quest_length", 5)
        self.quest_breadth = self.config.get("quest_breadth", 2)
        self.difficulty = self.config.get("difficulty", "medium")
        
        # Game state
        self.game = None
        self.game_state = None
        self.current_game_file = None
        
        # Action history
        self.action_history = []
        
        # Initialize environment
        self._initialize_environment()
        
        self.logger.info(f"Initialized TextWorld adapter: {env_id}")
    
    def _initialize_environment(self):
        """Initialize TextWorld environment."""
        try:
            # Set difficulty parameters
            difficulty_settings = {
                "easy": {"nb_objects": 5, "nb_rooms": 3, "quest_length": 3},
                "medium": {"nb_objects": 10, "nb_rooms": 5, "quest_length": 5},
                "hard": {"nb_objects": 15, "nb_rooms": 8, "quest_length": 8}
            }
            
            if self.difficulty in difficulty_settings:
                settings = difficulty_settings[self.difficulty]
                self.nb_objects = settings["nb_objects"]
                self.nb_rooms = settings["nb_rooms"]
                self.quest_length = settings["quest_length"]
            
            # Generate game
            if TEXTWORLD_AVAILABLE:
                self._generate_textworld_game()
            else:
                self.logger.warning("TextWorld not available, using mock environment")
                self._create_mock_environment()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TextWorld environment: {e}")
            self._create_mock_environment()
    
    def _generate_textworld_game(self):
        """Generate TextWorld game."""
        try:
            import textworld
            
            # Create game generation options
            options = textworld.GameOptions()
            options.seeds = self.random_seed
            options.nb_objects = self.nb_objects
            options.nb_rooms = self.nb_rooms
            options.quest_length = self.quest_length
            options.quest_breadth = self.quest_breadth
            
            # Generate game
            game = textworld.generator.make_game(options)
            
            # Compile game
            game_file = textworld.generator.compile_game(game)
            
            # Create environment
            env = textworld.start(game_file)
            
            self.game = game
            self.current_game_file = game_file
            self.tw_env = env
            
            self.logger.info("Successfully generated TextWorld game")
            
        except Exception as e:
            self.logger.error(f"Failed to generate TextWorld game: {e}")
            self._create_mock_environment()
    
    def _create_mock_environment(self):
        """Create mock environment when TextWorld is not available."""
        self.logger.info("Creating mock TextWorld environment")
        
        # Mock game state
        self.mock_state = {
            "location": "kitchen",
            "inventory": [],
            "locations": {
                "kitchen": {
                    "description": "You are in a kitchen. There is a fridge here.",
                    "items": ["apple", "key"],
                    "exits": ["north"]
                },
                "living_room": {
                    "description": "You are in a living room. There is a sofa here.",
                    "items": ["book"],
                    "exits": ["south", "east"]
                },
                "bedroom": {
                    "description": "You are in a bedroom. There is a bed and a chest here.",
                    "items": ["pillow"],
                    "exits": ["west"]
                }
            },
            "goal": "Find the key and open the chest in the bedroom.",
            "step_count": 0,
            "max_steps": self.max_episode_steps
        }
        
        self.is_mock = True
    
    def reset(self) -> str:
        """Reset environment."""
        self.state.reset()
        self.action_history.clear()
        
        if hasattr(self, 'is_mock') and self.is_mock:
            return self._mock_reset()
        
        try:
            if hasattr(self, 'tw_env'):
                game_state = self.tw_env.reset()
                self.game_state = game_state
                observation = game_state.feedback
            else:
                observation = "You are in a text-based adventure game."
            
            self.state.current_observation = observation
            self.state.episode_step = 0
            self.state.is_done = False
            self.state.episode_reward = 0.0
            
            self.logger.debug("Environment reset")
            return observation
            
        except Exception as e:
            self.logger.error(f"Error resetting environment: {e}")
            return self._mock_reset()
    
    def _mock_reset(self) -> str:
        """Mock environment reset."""
        self.mock_state["location"] = "kitchen"
        self.mock_state["inventory"] = []
        self.mock_state["step_count"] = 0
        
        # Reset item locations
        self.mock_state["locations"]["kitchen"]["items"] = ["apple", "key"]
        self.mock_state["locations"]["living_room"]["items"] = ["book"]
        self.mock_state["locations"]["bedroom"]["items"] = ["pillow"]
        
        observation = (f"{self.mock_state['locations']['kitchen']['description']} "
                      f"Goal: {self.mock_state['goal']}")
        
        self.state.current_observation = observation
        self.state.episode_step = 0
        self.state.is_done = False
        self.state.episode_reward = 0.0
        
        return observation
    
    def step(self, action: str) -> Tuple[str, float, bool, Dict[str, Any]]:
        """Execute action."""
        self.action_history.append(action)
        self.state.episode_step += 1
        
        if hasattr(self, 'is_mock') and self.is_mock:
            return self._mock_step(action)
        
        try:
            if hasattr(self, 'tw_env'):
                game_state, reward, done = self.tw_env.step(action)
                observation = game_state.feedback
                info = {"admissible_commands": game_state.admissible_commands}
            else:
                observation = f"You tried to {action}."
                reward = 0.0
                done = self.state.episode_step >= self.max_episode_steps
                info = {}
            
            self.state.current_observation = observation
            self.state.episode_reward += reward
            self.state.is_done = done
            
            if done:
                self._update_episode_stats(reward > 0)
            
            return observation, reward, done, info
            
        except Exception as e:
            self.logger.error(f"Error executing action '{action}': {e}")
            return self._mock_step(action)
    
    def _mock_step(self, action: str) -> Tuple[str, float, bool, Dict[str, Any]]:
        """Mock environment step."""
        action = action.lower().strip()
        reward = 0.0
        done = False
        info = {}
        
        current_location = self.mock_state["location"]
        location_data = self.mock_state["locations"][current_location]
        
        # Parse action
        if action.startswith("go "):
            direction = action[3:]
            reward, done, observation = self._mock_move(direction)
        elif action.startswith("take "):
            item = action[5:]
            reward, done, observation = self._mock_take(item)
        elif action == "look" or action == "examine room":
            observation = self._mock_look()
        elif action == "inventory":
            observation = f"You are carrying: {', '.join(self.mock_state['inventory']) if self.mock_state['inventory'] else 'nothing'}"
        elif action.startswith("open ") or action.startswith("use key on "):
            item = "chest" if "chest" in action else action.split()[-1]
            reward, done, observation = self._mock_open(item)
        else:
            observation = f"I don't understand '{action}'. Try: go <direction>, take <item>, look, inventory, open <item>"
            reward = -0.1
        
        # Check step limit
        self.mock_state["step_count"] += 1
        if self.mock_state["step_count"] >= self.mock_state["max_steps"]:
            done = True
            if reward == 0:
                reward = -1.0
        
        self.state.current_observation = observation
        self.state.episode_reward += reward
        self.state.is_done = done
        
        return observation, reward, done, info
    
    def _mock_move(self, direction: str) -> Tuple[float, bool, str]:
        """Mock movement."""
        current_location = self.mock_state["location"]
        location_data = self.mock_state["locations"][current_location]
        
        direction_map = {"north": "living_room", "south": "kitchen", "east": "bedroom", "west": "living_room"}
        
        if direction in direction_map and direction in location_data["exits"]:
            new_location = direction_map[direction]
            self.mock_state["location"] = new_location
            new_location_data = self.mock_state["locations"][new_location]
            return 0.0, False, new_location_data["description"]
        else:
            return -0.1, False, f"You can't go {direction} from here."
    
    def _mock_take(self, item: str) -> Tuple[float, bool, str]:
        """Mock item taking."""
        current_location = self.mock_state["location"]
        location_data = self.mock_state["locations"][current_location]
        
        if item in location_data["items"]:
            location_data["items"].remove(item)
            self.mock_state["inventory"].append(item)
            return 0.1, False, f"You take the {item}."
        else:
            return -0.1, False, f"There is no {item} here."
    
    def _mock_look(self) -> str:
        """Mock looking."""
        current_location = self.mock_state["location"]
        location_data = self.mock_state["locations"][current_location]
        
        description = location_data["description"]
        if location_data["items"]:
            description += f" You see: {', '.join(location_data['items'])}."
        
        return description
    
    def _mock_open(self, item: str) -> Tuple[float, bool, str]:
        """Mock opening items."""
        if item == "chest" and self.mock_state["location"] == "bedroom":
            if "key" in self.mock_state["inventory"]:
                return 1.0, True, "You open the chest with the key and find a treasure! You win!"
            else:
                return -0.1, False, "The chest is locked. You need a key."
        else:
            return -0.1, False, f"You can't open the {item}."
    
    def get_available_actions(self) -> List[str]:
        """Get available actions."""
        if hasattr(self, 'is_mock') and self.is_mock:
            return self._mock_get_available_actions()
        
        try:
            if hasattr(self, 'game_state') and self.game_state:
                return list(self.game_state.admissible_commands)
            else:
                return ["look", "inventory", "go north", "go south", "go east", "go west", 
                       "take apple", "take key", "take book", "open chest"]
        except:
            return self._mock_get_available_actions()
    
    def _mock_get_available_actions(self) -> List[str]:
        """Get mock environment available actions."""
        actions = ["examine room", "inventory"]
        
        current_location = self.mock_state["location"]
        location_data = self.mock_state["locations"][current_location]
        
        # Add movement actions
        for exit_dir in location_data["exits"]:
            actions.append(f"go {exit_dir}")
        
        # Add take actions
        for item in location_data["items"]:
            actions.append(f"take {item}")
        
        # Add special actions
        if current_location == "bedroom":
            actions.append("use key on door")
            actions.append("open chest")
        
        return actions
