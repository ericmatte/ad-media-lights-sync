# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
or any other method with the owners of this repository before making a change.

## Our vision for this application

This simple app was built to simply synchronize the color of RGB lights with the thumbnail of a media player linked to Home Assistant, without needing much configuration.

The app shall remain simple with that focused task in mind.

## Local development

1. Clone this repository.
1. Run `pip3 install -r requirements.txt`.
1. Edit code, add tests and run `pytest`.

### Testing on a Home Assistant instance

1. Copy the [`media_lights_sync`](./apps/media_lights_sync) folder into `appdaemon/apps/` on your Home Assistant instance.
1. Update `appdaemon/apps/apps.yaml` with the proper configuration for your setup (see [`info.md`](./info.md)).

## Pull Request Process

1. Ensure that the proposed changes do not break the current functionalities ot the app.
1. Update the `README.md` and `indo.md` with details of changes to the configuration or setup.
1. If breaking changes are needed, make sure to specify exactly what needs to change.

For new version, the versioning scheme we use is [SemVer](http://semver.org/).
