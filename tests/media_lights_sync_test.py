import pytest
import logging
import contextlib
import os

from appdaemontestframework import automation_fixture
from apps.media_lights_sync.media_lights_sync import MediaLightsSync, PICTURE_ATTRIBUTES
from PIL import Image

test_light_1_base_state = {'brightness': 50, 'rgb_color': [123, 123, 123]}

rgb_images = [
    "file://" + os.path.abspath("./examples/example-1.jpg"),
    "file://" + os.path.abspath("./examples/example-2.jpg"),
]
rgba_images = {
    "4kBigFile": "file://" + os.path.abspath("./tests/rgba_4k.png"),
    "nyanCat": "file://" + os.path.abspath("./tests/rgba_nyan_cat.png"),
}


@pytest.fixture
def hass_logs(hass_mocks):
    return lambda: [call[0][0] for call in hass_mocks.hass_functions["log"].call_args_list]


@pytest.fixture
def hass_errors(hass_mocks):
    return lambda: [call[0][0] for call in hass_mocks.hass_functions["error"].call_args_list]


@pytest.fixture
def media_lights_sync(given_that):
    mls = MediaLightsSync(None, None, None, None, None, None, None)
    given_that.passed_arg('media_player').is_set_to('media_player.tv_test')
    given_that.passed_arg('lights').is_set_to(['light.test_light_1', 'light.test_light_2'])

    given_that.state_of('light.test_light_1').is_set_to('on', test_light_1_base_state)
    given_that.state_of('light.test_light_2').is_set_to('off')
    mls.initialize()
    return mls


@pytest.fixture
def update_passed_args(media_lights_sync):
    @contextlib.contextmanager
    def update_and_init():
        yield
        media_lights_sync.initialize()

    return update_and_init


@pytest.fixture
def media_player(media_lights_sync, given_that):
    class UpdateState:
        def __init__(self, entity):
            self.entity = entity

        def update_state(self, state, attributes=None):
            given_that.state_of(self.entity).is_set_to(state, attributes)
            if attributes is None:
                current_attribute = PICTURE_ATTRIBUTES[0]
                old_url = rgb_images[0]
                new_url = None
            else:
                current_attribute = next(attr for attr in PICTURE_ATTRIBUTES if attributes.get(attr, None) is not None)
                old_url = None
                new_url = attributes[current_attribute]
            media_lights_sync.change_lights_color(self.entity, current_attribute, old_url, new_url, None)

    return UpdateState


class TestCallbacks:
    def test_callbacks_are_set_for_single_entity(self, media_lights_sync, assert_that, hass_logs):
        assert any(('Listening' in log and 'media_player.tv_test' in log) for log in hass_logs())

        for photo_attribute in PICTURE_ATTRIBUTES:
            assert_that(media_lights_sync).\
                listens_to.state('media_player.tv_test', attribute=photo_attribute).\
                with_callback(media_lights_sync.change_lights_color)

    def test_callbacks_are_set_for_multiple_entities(self, given_that, media_lights_sync, assert_that, update_passed_args):
        media_players = ['media_player.tv_test1', 'media_player.tv_test2']
        with update_passed_args():
            given_that.passed_arg('media_player').is_set_to(media_players)

        for media_player in media_players:
            for photo_attribute in PICTURE_ATTRIBUTES:
                assert_that(media_lights_sync).\
                    listens_to.state(media_player, attribute=photo_attribute).\
                    with_callback(media_lights_sync.change_lights_color)


class TestExtractImageColors:
    quantization_methods = [None, "FastOctree", "MedianCut", "MaxCoverage", "libimagequant"]

    def test_can_extract_colors(self, media_lights_sync):
        colors = media_lights_sync.get_colors(rgb_images[0])

        assert len(colors) == 2
        assert len(colors[0]) == 3
        assert len(colors[1]) == 3

    def test_can_extract_colors_on_rgba_image_with_mediancut(self, media_lights_sync, update_passed_args, given_that):
        with update_passed_args():
            given_that.passed_arg('quantization_method').is_set_to('MedianCut')

        colors = media_lights_sync.get_colors(rgba_images["4kBigFile"])

        assert len(colors) == 2
        assert len(colors[0]) == 3
        assert len(colors[1]) == 3

    def test_all_quantization_methods_on_rgb_image(self, media_lights_sync, update_passed_args, given_that):
        for method in self.quantization_methods:
            with update_passed_args():
                given_that.passed_arg('quantization_method').is_set_to(method)

            colors = media_lights_sync.get_colors(rgb_images[0])

            assert len(colors) == 2
            assert len(colors[0]) == 3
            assert len(colors[1]) == 3

    def test_all_quantization_methods_on_rgba_image(self, media_lights_sync, update_passed_args, given_that):
        for method in self.quantization_methods:
            with update_passed_args():
                given_that.passed_arg('quantization_method').is_set_to(method)

            colors = media_lights_sync.get_colors(rgba_images["nyanCat"])

            assert len(colors) == 2
            assert len(colors[0]) == 3
            assert len(colors[1]) == 3


def test_can_change_lights(assert_that, media_player, given_that):
    media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[0]})

    assert_that('light.test_light_1').was.turned_on(brightness=255, rgb_color=[59, 180, 180])
    assert_that('light.test_light_2').was.turned_on(brightness=255, rgb_color=[46, 56, 110])
    given_that.mock_functions_are_cleared()

    media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[1]})

    assert_that('light.test_light_1').was.turned_on(brightness=255, rgb_color=[153, 68, 106])
    assert_that('light.test_light_2').was.turned_on(brightness=255, rgb_color=[111, 11, 24])


def test_calling_twice_skips_color_extraction(media_player, hass_logs, hass_mocks):
    media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[0], "entity_picture_local": rgb_images[0]})
    media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[0], "entity_picture_local": rgb_images[0]})

    assert len(hass_mocks.hass_functions["turn_on"].call_args_list) == 2
    assert "skipped" in hass_logs()[-1]


class TestResetLights:
    def test_can_reset_lights(self, given_that, media_player, assert_that, update_passed_args):
        with update_passed_args():
            given_that.passed_arg('reset_lights_after').is_set_to(True)
        media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[0]})
        given_that.mock_functions_are_cleared()

        media_player('media_player.tv_test').update_state('idle')

        assert_that('light.test_light_2').was.turned_off()
        assert_that('light.test_light_1').was.turned_on(**test_light_1_base_state)

    def test_wont_reset_lights_if_setting_is_false(self, given_that, media_player, hass_mocks):
        media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[0]})
        given_that.mock_functions_are_cleared()

        media_player('media_player.tv_test').update_state('idle')

        assert len(hass_mocks.hass_functions["turn_on"].call_args_list) == 0

    def test_can_change_lights_after_reset(self, assert_that, media_player, given_that, update_passed_args):
        with update_passed_args():
            given_that.passed_arg('reset_lights_after').is_set_to(True)
        media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[0]})
        media_player('media_player.tv_test').update_state('idle')
        given_that.mock_functions_are_cleared()

        media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[0]})

        assert_that('light.test_light_1').was.turned_on(brightness=255, rgb_color=[59, 180, 180])
        assert_that('light.test_light_2').was.turned_on(brightness=255, rgb_color=[46, 56, 110])


class TestURLErrors:
    def test_url_error_are_handled(self, media_player, hass_errors, hass_mocks):
        invalide_image = "file:///example-404.jpg"
        media_player('media_player.tv_test').update_state('playing', {"entity_picture": invalide_image})

        assert any('Unable to fetch artwork' in log for log in hass_errors())
        assert len(hass_mocks.hass_functions["turn_on"].call_args_list) == 0

    def test_http_error_are_handled(self, media_player, hass_errors, hass_mocks):
        image_404 = "https://raw.githubusercontent.com/ericmatte/ad-media-lights-sync/master/examples/example-404.jpg"
        media_player('media_player.tv_test').update_state('playing', {"entity_picture": image_404})

        assert any('Unable to fetch artwork' in log for log in hass_errors())
        assert len(hass_mocks.hass_functions["turn_on"].call_args_list) == 0


def test_can_saturate_colors(given_that, media_lights_sync, media_player, assert_that, update_passed_args):
    base_color = [59, 180, 180]
    saturated_color = media_lights_sync.get_saturated_color(base_color)
    with update_passed_args():
        given_that.passed_arg('use_saturated_colors').is_set_to(True)

    media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[0]})

    assert_that('light.test_light_1').was_not.turned_on(brightness=255, rgb_color=base_color)
    assert_that('light.test_light_1').was.turned_on(brightness=255, rgb_color=saturated_color)


def test_givin_wrong_method_use_defaults(given_that, media_lights_sync, hass_logs, update_passed_args):
    with update_passed_args():
        given_that.passed_arg('quantization_method').is_set_to('InvalidMethod')

    assert any('Using default' in log for log in hass_logs())
    assert media_lights_sync.quantization_method is None


class TestBrightness:
    def test_full_brightness_by_default(self, media_player, assert_that):
        media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[0]})

        assert_that('light.test_light_1').was.turned_on(brightness=255, rgb_color=[59, 180, 180])
        assert_that('light.test_light_2').was.turned_on(brightness=255, rgb_color=[46, 56, 110])

    def test_keep_current_brightness(self, given_that, media_player, assert_that, update_passed_args):
        with update_passed_args():
            given_that.passed_arg('use_current_brightness').is_set_to(True)

        media_player('media_player.tv_test').update_state('playing', {"entity_picture": rgb_images[0]})

        assert_that('light.test_light_1').was.turned_on(rgb_color=[59, 180, 180])
        assert_that('light.test_light_2').was.turned_on(rgb_color=[46, 56, 110])


class TestConditions:
    condition_entity_id = 'input_boolean.sync_tv_lights'

    @pytest.fixture
    def conditional_media_lights_sync(self, media_lights_sync, given_that, update_passed_args):
        with update_passed_args():
            given_that.passed_arg('condition').is_set_to({"entity": self.condition_entity_id, "state": "on"})
        return media_lights_sync

    def test_can_change_if_no_condition(self, media_lights_sync):
        assert media_lights_sync.can_change_colors() == True

    def test_can_change_if_condition_is_met(self, given_that, conditional_media_lights_sync):
        given_that.state_of(self.condition_entity_id).is_set_to('on')
        assert conditional_media_lights_sync.can_change_colors() == True

    def test_wont_change_if_condition_is_false(self, given_that, conditional_media_lights_sync):
        given_that.state_of(self.condition_entity_id).is_set_to('false')
        assert conditional_media_lights_sync.can_change_colors() == False


class TestFormatUrl:
    relative_url = "/api/media_player_proxy/media_player.tv_test"

    def test_relative_url_without_ha_url_throws(self, media_lights_sync):
        with pytest.raises(ValueError):
            media_lights_sync.format_url(self.relative_url, "media_player.tv_test", PICTURE_ATTRIBUTES[0])

    def test_relative_url_with_ha_url(self, given_that, media_lights_sync, update_passed_args):
        ha_url = "http://192.168.1.123:8123"
        with update_passed_args():
            given_that.passed_arg('ha_url').is_set_to(ha_url)

        formatted_url = media_lights_sync.format_url(self.relative_url, "media_player.tv_test", PICTURE_ATTRIBUTES[0])

        assert formatted_url == ha_url + self.relative_url

    def test_full_url(self, given_that, media_lights_sync, update_passed_args):
        ha_url = "https://my-ha.duckdns.org/api/media_player_proxy/media_player.tv_test"
        with update_passed_args():
            given_that.passed_arg('ha_url').is_set_to(ha_url)

        formatted_url = media_lights_sync.format_url(self.relative_url, "media_player.tv_test", PICTURE_ATTRIBUTES[0])

        assert formatted_url == ha_url
