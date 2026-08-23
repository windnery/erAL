def test_lap_pillow_is_unavailable_outdoors(world):
    # Given: a qualified shipgirl is beside the player on an outdoor street.
    world.player.location = {'region': 'shop_street', 'node': 'street'}
    npc = world.npc_manager.get_npc_by_id('Z23')
    world.npc_manager.set_loc(npc.id, 'shop_street', 'street')
    npc.cflag['sleeping'] = False
    npc.set_talent('relationship', '2')

    # When: the lap-pillow command availability is evaluated.
    from game_engine.commands.interact.request_a_lap_pillow import can

    is_available = can(world, npc)

    # Then: the outdoor location rejects the command.
    assert is_available is False
