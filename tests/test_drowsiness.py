def test_drowsiness_drains_player_resources_over_time(world):
    # Given: the player has been awake for sixteen hours and has entered drowsiness.
    world.time_manager.hour = 23
    world.time_manager.minute = 0
    world.player.set_stamina(100)
    world.player.set_energy(100)

    # When: ten active minutes pass.
    world.advance_time_with_events(10)

    # Then: stamina and energy each fall by one point per minute.
    assert world.player.get_stamina() == 90
    assert world.player.get_energy() == 90


def test_drowsiness_only_charges_minutes_after_its_start(world):
    # Given: five normal minutes remain before the drowsiness window starts.
    world.time_manager.hour = 22
    world.time_manager.minute = 55
    world.player.set_stamina(100)
    world.player.set_energy(100)

    # When: ten active minutes cross the drowsiness boundary.
    world.advance_time_with_events(10)

    # Then: only the five drowsy minutes consume resources.
    assert world.player.get_stamina() == 95
    assert world.player.get_energy() == 95
