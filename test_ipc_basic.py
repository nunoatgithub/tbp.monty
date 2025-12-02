#!/usr/bin/env python
"""Basic test script for IPC-based HabitatEnvironment."""

import logging
import os
from dataclasses import asdict

from tbp.monty.frameworks.config_utils.make_dataset_configs import (
    PatchAndViewFinderMountConfig,
)
from tbp.monty.simulators.habitat.ipc_environment import (
    AgentConfig,
    HabitatIPCEnvironment,
)
from tbp.monty.simulators.habitat import MultiSensorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_ipc():
    """Test basic IPC environment operations."""
    logger.info("Testing IPC-based HabitatEnvironment")
    
    # Create agent configuration
    agent_config = AgentConfig(
        agent_type=MultiSensorAgent,
        agent_args=PatchAndViewFinderMountConfig().__dict__,
    )
    
    # Create environment
    data_path = os.environ.get("MONTY_DATA", None)
    if data_path:
        data_path = os.path.join(data_path, "habitat/objects/ycb")
    
    logger.info(f"Creating HabitatIPCEnvironment with data_path={data_path}")
    env = HabitatIPCEnvironment(
        agents=agent_config,
        data_path=data_path,
        scene_id=None,
        seed=42,
    )
    
    try:
        # Test add object
        logger.info("Testing add_object")
        obj_id = env.add_object(
            name="coneSolid",
            position=(0.0, 1.5, -0.2),
        )
        logger.info(f"Added object with ID: {obj_id}")
        
        # Test reset
        logger.info("Testing reset")
        obs, state = env.reset()
        logger.info(f"Reset complete - got {len(obs)} agent observations")
        
        # Test remove all objects
        logger.info("Testing remove_all_objects")
        env.remove_all_objects()
        logger.info("Removed all objects")
        
        logger.info("✓ All basic tests passed!")
        
    finally:
        logger.info("Closing environment")
        env.close()
        logger.info("Environment closed")


if __name__ == "__main__":
    test_basic_ipc()
