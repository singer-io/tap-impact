# Changelog

## 2.1.0
  * Sets Default start_date to 3 Years Ago for actions and actionUpdates if it is older [#33](https://github.com/singer-io/tap-impact/pull/33)
  * Removes implementation of clicks stream as it is deprecated [#34](https://github.com/singer-io/tap-impact/pull/34)
  * Date window implementation for actions and actionUpdates [#35](https://github.com/singer-io/tap-impact/pull/35)

## 2.0.2
  * Adds end date in params for Actions and related streams [#31](https://github.com/singer-io/tap-impact/pull/31)

## 2.0.1
  * Dependabot update [#25](https://github.com/singer-io/tap-impact/pull/25)

## 2.0.0
  * Updates integer datatype to String in action_updates schema [#21](hhttps://github.com/singer-io/tap-impact/pull/21)

## 1.0.2
  * Sets empty string as default value for model_id if not configured [#23](https://github.com/singer-io/tap-impact/pull/23)

## 1.0.1
  * Fix model_id parsing error when it is not configured [#22](https://github.com/singer-io/tap-impact/pull/22)

## 1.0.0
  * Added circle, pylint, and bumped to 1.0.0 for GA release

## 0.0.4
  * Fix issue for `conversion_paths`. Increase JSON schema decimal digits to `multipleOf` = `1e-8`.

## 0.0.3
  * Add endpoint for `conversion_paths` and update documentation, which requires new optional `tap_config.json` parameter `model_id`.

## 0.0.2
  * Fix issue with Actions and Action Updates, replace reserved work column `oid` with `order_id`.

## 0.0.1
  * Initial commit