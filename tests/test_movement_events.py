def prepare_isolated_npcs(world) -> None:
    for npc in world.npc_manager.get_all_npcs():
        npc.schedule = {
            'sleep': {'start': [0, 0], 'end': [0, 0]},
            'works': [],
        }
        world.npc_manager.set_loc(npc.id, 'office', 'desk')


def test_departure_event_includes_destination(world, monkeypatch):
    # Given: Z23 is beside the player and starts work elsewhere after one minute.
    monkeypatch.setattr('game_engine.managers.NpcManager.randint', lambda start, end: 100)
    prepare_isolated_npcs(world)
    player_location = world.player.location.copy()
    z23 = world.npc_manager.get_npc_by_id('Z23')
    world.npc_manager.set_loc(z23.id, player_location['region'], player_location['node'])
    z23.schedule['works'] = [{
        'location': {'region': 'office', 'node': 'desk'},
        'time': {'start': [7, 1], 'end': [8, 0]},
    }]
    destination = (
        f"{world.map_manager.regions['office']['name']} · "
        f"{world.map_manager.maps['office']['desk']['name']}"
    )

    # When: time reaches the work schedule.
    events = world.advance_time_with_events(1)

    # Then: the departure tells the player where Z23 went.
    event = next(message for message in events if z23.name in message)
    assert destination in event


def test_arrival_event_includes_origin(world, monkeypatch):
    # Given: Z23 starts away from the player and is scheduled to work beside them.
    monkeypatch.setattr('game_engine.managers.NpcManager.randint', lambda start, end: 100)
    prepare_isolated_npcs(world)
    z23 = world.npc_manager.get_npc_by_id('Z23')
    origin = (
        f"{world.map_manager.regions['office']['name']} · "
        f"{world.map_manager.maps['office']['desk']['name']}"
    )
    z23.schedule['works'] = [{
        'location': world.player.location.copy(),
        'time': {'start': [7, 1], 'end': [8, 0]},
    }]

    # When: time reaches the work schedule.
    events = world.advance_time_with_events(1)

    # Then: the arrival tells the player where Z23 came from.
    event = next(message for message in events if z23.name in message)
    assert origin in event
