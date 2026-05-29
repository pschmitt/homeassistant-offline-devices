#!/usr/bin/env bash


get_auth_token() {
  cd "$(cd "$(dirname "$0")" >/dev/null 2>&1; pwd -P)" || exit 9
  sed -nr "s/HASS_TOKEN:\s*['\"]?([^'\"]+)['\"]?/\1/p" ../secrets.yaml
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
  cd "$(cd "$(dirname "$0")" >/dev/null 2>&1; pwd -P)" || exit 9

  if ! HASS_TOKEN="$(get_auth_token)"
  then
    echo "Failed to retrieve HASS token."
    exit 1
  fi

  export HASS_TOKEN

  case "$1" in
    restart-required)
      ./hass_ws.py repairs/list_issues | \
        jq -er '[.issues[] |
          select(
            .ignored == false and
            .domain == "hacs" and
            (.issue_id | test("^restart_required"))
          )] as $r |
          {
            "restart_required": (($r | length) > 0),
            "reason": (
              if ($r == [])
              then
                ""
              else (
                $r[] | "\(.domain)/\(.issue_domain)"
              )
              end
            ),
            "issues": $r
          }'
      ;;
    dev*)
      case "$2" in
        offline*)
          IGNORED_DEVICES="(Spare)|(Switchbot)"
          INTERMITTENT_DEVICES="[]"
          if INTERMITTENT_DEVICES="$(./hass_ws.py config/device_registry/list | \
            jq -er '[.[] | select((.labels // [] | index("intermittent")))]')"
          then
            :
          fi

          ./hass_ws.py config_entries/get | \
            jq -er --arg ign "$IGNORED_DEVICES" \
              --arg intermittent "$INTERMITTENT_DEVICES" \
              '
                ($intermittent | (try fromjson catch [])) as $intermittent_devices
                | ($intermittent_devices | map(.name_by_user // .name) | map(select(. != null))) as $intermittent_names
                | ($intermittent_devices | map(.id) | map(select(. != null))) as $intermittent_ids
                | (if type == "object" and (.result? != null) then .result else . end) as $entries
                | (
                    if ($entries | type) == "array"
                    then $entries
                    else [$entries]
                    end
                  ) as $entries_list
                |
                [
                  $entries_list[]
                  | select(type == "object")
                  | (.title // "") as $title
                  | select(
                      .state == "setup_retry" and
                      ($title | test($ign) | not) and
                      ($intermittent_names | index($title) | not) and
                      (
                        (.device_id // "") as $device_id
                        | $device_id == "" or ($intermittent_ids | index($device_id) | not)
                      )
                    )
                  | $title
                ]
                | sort as $devices
                | ($devices | length) as $count
                | {
                    "count": $count,
                    "devices": $devices,
                    "ignored_devices": ($ign | gsub("\\)\\|\\("; ", ") | sub("^\\((?<match>.+)\\)$"; "\(.match)")),
                    "intermittent_devices": ([$intermittent_devices | .[] | (.name_by_user // .name)] | join(", ")),
                    "msg": (if $count == 0 then "All good" else ($count | tostring) + " devices offline: " + ($devices | join(", ")) end),
                    "primary_info": (if $count == 0 then "All good" else $count | tostring + " devices offline" end),
                    "secondary_info": ($devices | join(", "))
                  }
              '
          ;;
        *)
          echo "Unknown subcommand: $2"
          exit 2
          ;;
      esac
      ;;
    matter)
      case "$2" in
        offline*)
          IGNORED_DEVICES="(Matter Server)"

          # Cache device registry – used for disabled + intermittent + device list
          DEVICE_REGISTRY="$(./hass_ws.py config/device_registry/list)"

          DISABLED_DEVICES="$(echo "$DEVICE_REGISTRY" | \
            jq -er '[.[] | select(any(.identifiers[]; .[0] == "matter") and .disabled_by != null)]')"

          INTERMITTENT_DEVICES="[]"
          if TMP="$(echo "$DEVICE_REGISTRY" | \
            jq -er '[.[] | select(any(.identifiers[]; .[0] == "matter") and (.labels // [] | index("intermittent")))]')"
          then
            INTERMITTENT_DEVICES="$TMP"
          fi

          MATTER_ENTITIES="$(./hass_ws.py config/entity_registry/list | \
            jq -er '[.[] | select(.platform == "matter" and .disabled_by == null)]')"

          MATTER_DEVICES="$(echo "$DEVICE_REGISTRY" | \
            jq -er '[.[] | select(any(.identifiers[]; .[0] == "matter"))]')"

          ./hass_ws.py get_states | \
            jq -er \
              --arg ign "$IGNORED_DEVICES" \
              --argjson disabled "$DISABLED_DEVICES" \
              --arg intermittent "$INTERMITTENT_DEVICES" \
              --argjson entities "$MATTER_ENTITIES" \
              --argjson all_devices "$MATTER_DEVICES" \
            '
              ($intermittent | (try fromjson catch [])) as $intermittent_devices
              | ($disabled | map(.id)) as $disabled_ids
              | ($intermittent_devices | map(.id)) as $intermittent_ids

              # Build state map: entity_id -> state
              | (map({(.entity_id): .state}) | add // {}) as $state_map

              # Build device → [entity_ids] map, excluding stateless event entities
              | (
                  $entities
                  | map(select(.entity_id | startswith("event.") | not))
                  | group_by(.device_id)
                  | map({key: .[0].device_id, value: [.[].entity_id]})
                  | from_entries
                ) as $device_entities

              | [
                  $all_devices[]
                  | select(
                      .disabled_by == null
                      and ((.name_by_user // .name // "") | test($ign) | not)
                      and (.id as $did | $disabled_ids | index($did) | not)
                      and (.id as $did | $intermittent_ids | index($did) | not)
                      and (
                          .id as $did
                          | ($device_entities[$did] // []) as $eids
                          | ($eids | length) > 0
                          and ($eids | map($state_map[.] == "unavailable") | all)
                        )
                    )
                  | {
                      "name": (.name_by_user // .name),
                      "id": .id
                    }
                ]
              | {
                  "count": length,
                  "devices": ([.[].name] | join(", ")),
                  "ignored_devices": ($ign | gsub("\\)\\|\\("; ", ") | sub("^\\((?<match>.+)\\)$"; "\(.match)")),
                  "disabled_devices": ([$disabled[] | (.name_by_user // .name)] | join(", ")),
                  "intermittent_devices": ([$intermittent_devices[] | (.name_by_user // .name)] | join(", ")),
                  "msg": (if length == 0 then "" else "Offline Matter devices: " + ([.[].name] | join(", ")) end),
                  "primary_info": (if length == 0 then "All Matter devices online" else "Some Matter devices are offline" end),
                  "secondary_info": ([.[].name] | join(", "))
                }
            '
          ;;
        *)
          echo "Unknown subcommand: $2"
          exit 2
          ;;
      esac
      ;;
    generic)
      case "$2" in
        offline*)
          IGNORED_DEVICES=""

          # Cache device registry once
          DEVICE_REGISTRY="$(./hass_ws.py config/device_registry/list)"

          # All devices not handled by ZHA or Matter (those have dedicated sensors)
          GENERIC_DEVICES="$(echo "$DEVICE_REGISTRY" | \
            jq -er '[.[] |
              select(
                .disabled_by == null and
                (any(.identifiers[]; .[0] == "zha") | not) and
                (any(.identifiers[]; .[0] == "matter") | not)
              )
            ]')"

          GENERIC_DEVICE_IDS="$(echo "$GENERIC_DEVICES" | \
            jq -er '[.[].id]')"

          DISABLED_DEVICES="$(echo "$DEVICE_REGISTRY" | \
            jq -er --argjson ids "$GENERIC_DEVICE_IDS" \
              '[.[] | select((.id as $id | $ids | index($id) != null) and .disabled_by != null)]')"

          INTERMITTENT_DEVICES="[]"
          if TMP="$(echo "$DEVICE_REGISTRY" | \
            jq -er --argjson ids "$GENERIC_DEVICE_IDS" \
              '[.[] | select((.id as $id | $ids | index($id) != null) and (.labels // [] | index("intermittent")))]')"
          then
            INTERMITTENT_DEVICES="$TMP"
          fi

          # Meaningful entities: non-diagnostic, non-event, enabled, attached to a device
          GENERIC_ENTITIES="$(./hass_ws.py config/entity_registry/list | \
            jq -er --argjson ids "$GENERIC_DEVICE_IDS" '[.[] |
              select(
                .disabled_by == null and
                .entity_category == null and
                (.entity_id | startswith("event.") | not) and
                .device_id != null and
                (.device_id as $did | $ids | index($did) != null)
              )
            ]')"

          ./hass_ws.py get_states | \
            jq -er \
              --arg ign "$IGNORED_DEVICES" \
              --argjson disabled "$DISABLED_DEVICES" \
              --arg intermittent "$INTERMITTENT_DEVICES" \
              --argjson entities "$GENERIC_ENTITIES" \
              --argjson all_devices "$GENERIC_DEVICES" \
            '
              ($intermittent | (try fromjson catch [])) as $intermittent_devices
              | ($disabled | map(.id)) as $disabled_ids
              | ($intermittent_devices | map(.id)) as $intermittent_ids

              | (map({(.entity_id): .state}) | add // {}) as $state_map

              | (
                  $entities
                  | group_by(.device_id)
                  | map({key: .[0].device_id, value: [.[].entity_id]})
                  | from_entries
                ) as $device_entities

              | [
                  $all_devices[]
                  | select(
                      .disabled_by == null
                      and (.id as $did | $disabled_ids | index($did) | not)
                      and (.id as $did | $intermittent_ids | index($did) | not)
                      and (
                          if ($ign | length) > 0
                          then ((.name_by_user // .name // "") | test($ign) | not)
                          else true
                          end
                        )
                      and (
                          .id as $did
                          | ($device_entities[$did] // []) as $eids
                          | ($eids | length) > 0
                          and ($eids | map($state_map[.] == "unavailable") | all)
                        )
                    )
                  | {
                      "name": (.name_by_user // .name),
                      "id": .id
                    }
                ]
              | {
                  "count": length,
                  "devices": ([.[].name] | join(", ")),
                  "ignored_devices": (if ($ign | length) > 0 then ($ign | gsub("\\)\\|\\("; ", ") | sub("^\\((?<match>.+)\\)$"; "\(.match)")) else "" end),
                  "disabled_devices": ([$disabled[] | (.name_by_user // .name)] | join(", ")),
                  "intermittent_devices": ([$intermittent_devices[] | (.name_by_user // .name)] | join(", ")),
                  "msg": (if length == 0 then "" else "Offline devices: " + ([.[].name] | join(", ")) end),
                  "primary_info": (if length == 0 then "All devices online" else "Some devices are offline" end),
                  "secondary_info": ([.[].name] | join(", "))
                }
            '
          ;;
        *)
          echo "Unknown subcommand: $2"
          exit 2
          ;;
      esac
      ;;
    zha|zigbee)
      case "$2" in
        offline*)
          IGNORED_DEVICES="(SONOFF 01MINIZB)|(TRADFRI SHORTCUT Button)|(Aqara Opple 6 button remote)"
          # DISABLED_DEVICES="$(hass-cli -o json device list | \
          #   jq -er '[.[] | select(any(.identifiers[]; .[] == "zha") and .disabled_by != null)]')"
          DISABLED_DEVICES="$(./hass_ws.py config/device_registry/list | \
            jq -er '[.[] | select(any(.identifiers[]; .[] == "zha") and .disabled_by != null)]')"
          INTERMITTENT_DEVICES="[]"
          if INTERMITTENT_DEVICES="$(./hass_ws.py config/device_registry/list | \
            jq -er '[.[] | select(any(.identifiers[]; .[] == "zha") and (.labels // [] | index("intermittent")))]')"
          then
            :
          fi

          ./hass_ws.py zha/devices | \
            jq -er --arg ign "$IGNORED_DEVICES" \
              --argjson disabled "$DISABLED_DEVICES" \
              --arg intermittent "$INTERMITTENT_DEVICES" \
            '
              ($intermittent | (try fromjson catch [])) as $intermittent_devices
              | ( $disabled
                | map(
                    .identifiers[]
                    | select(.[0]=="zha")
                    | .[1]
                  )
              ) as $disabled_ieees
              | ( $intermittent_devices
                | map(
                    .identifiers[]
                    | select(.[0]=="zha")
                    | .[1]
                  )
              ) as $intermittent_ieees

              | [
                .[]
                | .ieee as $ieee

                | select(
                  # is offline?
                  .available == false and

                  # Check if ignored
                  (.name | test($ign) | not) and
                  (.user_given_name // "" | test($ign) | not) and

                  # Check if disabled
                  ($disabled_ieees | index($ieee) | not) and

                  # Check if intermittent
                  ($intermittent_ieees | index($ieee) | not)
                )
                | {
                    "name": (.user_given_name // .name),
                    "last_seen": .last_seen
                  }
              ]
              | {
                  "count": length,
                  "devices": ([.[].name] | join(", ")),
                  "ignored_devices": ($ign | gsub("\\)\\|\\("; ", ") | sub("^\\((?<match>.+)\\)$"; "\(.match)")),
                  "disabled_devices": ([$disabled | .[].name_by_user] | join(", ")),
                  "intermittent_devices": ([$intermittent_devices | .[].name_by_user] | join(", ")),
                  "msg": (if length == 0 then "" else "Offline devices: " + ([.[].name] | join(", ")) end),
                  "primary_info": (if length == 0 then "All ZHA devices online" else "Some ZHA devices are offline" end),
                  "secondary_info": ([.[].name] | join(", "))
                }
            '
          ;;
        *)
          echo "Unknown subcommand: $2"
          exit 2
          ;;
      esac
      ;;
  esac
fi

# vim: set ft=bash et ts=2 sw=2 :
