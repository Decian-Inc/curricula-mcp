# Tool catalog

All list tools accept the API's supported JSON:API `query` filters, pagination, sorting, and includes. Identifiers belong in `path_params`; write payloads belong in `body`.

## Accounts

- `list_accounts` — Find accounts available to the authenticated administrator.
- `get_account` — Inspect an account's details.
- `delete_account` — Permanently remove an account.
- `list_account_assignments` — Review an account's training assignments.
- `list_account_departments` — Review departments in an account.
- `list_account_groups` — Review learner groups in an account.
- `list_account_learners` — Review learners in an account.
- `list_account_phishing_campaigns` — Review an account's phishing campaigns.
- `list_account_phishing_scenarios` — Review an account's phishing scenarios.
- `list_account_admin_users` — Review administrators for an account.
- `list_account_summary_reports_for_account` — Retrieve summary reports for one account.

## Reports and assignments

- `list_account_summary_reports` — Find account summary reports across accessible accounts.
- `get_account_summary_report` — Inspect an account summary report.
- `list_assignments` — Find training assignments.
- `create_assignment` — Create a training assignment with a JSON:API payload.
- `get_assignment` — Inspect a training assignment.
- `add_learner_to_assignment` — Enroll a learner through an assignment enrollment extra.
- `add_group_to_assignment` — Enroll a group through an assignment enrollment condition.
- `list_assignment_learners` — See learners enrolled in an assignment.
- `get_assignment_learner_activity` — Review a learner's activity on an assignment.
- `get_assignment_completion_certificate` — Retrieve a learner's completion certificate.
- `list_assignment_enrollment_conditions` — Review assignment enrollment conditions.
- `list_assignment_enrollment_extras` — Review additional enrollment information.

## Learners and training content

- `list_departments` — Find departments.
- `get_department` — Inspect a department.
- `list_episodes` — Find training episodes.
- `get_episode` — Inspect a training episode.
- `list_groups` — Find learner groups.
- `create_group` — Create a learner group with a JSON:API payload.
- `get_group` — Inspect a learner group.
- `move_learner_to_group` — Move a learner into a group.
- `remove_learner_from_group` — Remove a learner from its group.
- `list_learners` — Find learners.
- `get_learner` — Inspect a learner.

## Phishing

- `list_phishing_campaigns` — Find phishing campaigns.
- `get_phishing_campaign` — Inspect a phishing campaign.
- `list_phishing_campaign_attempts` — Review attempts made in a campaign.
- `list_phishing_campaign_scenarios` — Review scenarios used by a campaign.
- `get_phishing_campaign_scenario` — Inspect a campaign-scenario record.
- `list_phishing_campaign_scenario_attempts` — Review attempts for a campaign-scenario.
- `get_phishing_campaign_scenario_campaign` — Retrieve the campaign for a campaign-scenario.
- `get_phishing_campaign_scenario_scenario` — Retrieve the scenario for a campaign-scenario.
- `report_phishing_attempt` — Mark a phishing attempt as reported using its code or message ID.
- `list_phishing_scenarios` — Find phishing scenarios.
- `get_phishing_scenario` — Inspect a phishing scenario.

## Admin users

- `list_admin_users` — Find administrator users.
- `create_admin_user` — Create an administrator user with a JSON:API payload.
- `get_admin_user` — Inspect an administrator user.
- `update_admin_user` — Update an administrator user with a JSON:API payload.
- `delete_admin_user` — Permanently remove an administrator user.
