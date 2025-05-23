import pytest
from django.conf import settings
from infi.clickhouse_orm import Database
from unittest.mock import patch

from posthog.clickhouse.client import sync_execute
from posthog.test.base import PostHogTestCase, run_clickhouse_statement_in_parallel


def create_clickhouse_tables():
    # Create clickhouse tables to default before running test
    # Mostly so that test runs locally work correctly
    from posthog.clickhouse.schema import (
        CREATE_DATA_QUERIES,
        CREATE_DICTIONARY_QUERIES,
        CREATE_DISTRIBUTED_TABLE_QUERIES,
        CREATE_KAFKA_TABLE_QUERIES,
        CREATE_MERGETREE_TABLE_QUERIES,
        CREATE_MV_TABLE_QUERIES,
        CREATE_VIEW_QUERIES,
        build_query,
    )

    num_expected_tables = (
        len(CREATE_MERGETREE_TABLE_QUERIES)
        + len(CREATE_DISTRIBUTED_TABLE_QUERIES)
        + len(CREATE_MV_TABLE_QUERIES)
        + len(CREATE_VIEW_QUERIES)
        + len(CREATE_DICTIONARY_QUERIES)
    )

    # Evaluation tests use Kafka for faster data ingestion.
    if settings.IN_EVAL_TESTING:
        num_expected_tables += len(CREATE_KAFKA_TABLE_QUERIES)

    [[num_tables]] = sync_execute(
        "SELECT count() FROM system.tables WHERE database = %(database)s",
        {"database": settings.CLICKHOUSE_DATABASE},
    )

    # Check if all the tables have already been created. Views, materialized views, and dictionaries also count
    if num_tables == num_expected_tables:
        return

    table_queries = list(map(build_query, CREATE_MERGETREE_TABLE_QUERIES + CREATE_DISTRIBUTED_TABLE_QUERIES))
    run_clickhouse_statement_in_parallel(table_queries)

    if settings.IN_EVAL_TESTING:
        kafka_table_queries = list(map(build_query, CREATE_KAFKA_TABLE_QUERIES))
        run_clickhouse_statement_in_parallel(kafka_table_queries)

    mv_queries = list(map(build_query, CREATE_MV_TABLE_QUERIES))
    run_clickhouse_statement_in_parallel(mv_queries)

    view_queries = list(map(build_query, CREATE_VIEW_QUERIES))
    run_clickhouse_statement_in_parallel(view_queries)

    dictionary_queries = list(map(build_query, CREATE_DICTIONARY_QUERIES))
    run_clickhouse_statement_in_parallel(dictionary_queries)

    data_queries = list(map(build_query, CREATE_DATA_QUERIES))
    run_clickhouse_statement_in_parallel(data_queries)


def reset_clickhouse_tables():
    # Truncate clickhouse tables to default before running test
    # Mostly so that test runs locally work correctly
    from posthog.clickhouse.dead_letter_queue import (
        TRUNCATE_DEAD_LETTER_QUEUE_TABLE_SQL,
    )
    from posthog.clickhouse.plugin_log_entries import (
        TRUNCATE_PLUGIN_LOG_ENTRIES_TABLE_SQL,
    )
    from posthog.heatmaps.sql import TRUNCATE_HEATMAPS_TABLE_SQL
    from posthog.models.ai.pg_embeddings import TRUNCATE_PG_EMBEDDINGS_TABLE_SQL
    from posthog.models.app_metrics.sql import TRUNCATE_APP_METRICS_TABLE_SQL
    from posthog.models.channel_type.sql import TRUNCATE_CHANNEL_DEFINITION_TABLE_SQL
    from posthog.models.cohort.sql import TRUNCATE_COHORTPEOPLE_TABLE_SQL
    from posthog.models.error_tracking.sql import TRUNCATE_ERROR_TRACKING_ISSUE_FINGERPRINT_OVERRIDES_TABLE_SQL
    from posthog.models.event.sql import TRUNCATE_EVENTS_RECENT_TABLE_SQL, TRUNCATE_EVENTS_TABLE_SQL
    from posthog.models.exchange_rate.sql import TRUNCATE_EXCHANGE_RATE_TABLE_SQL
    from posthog.models.group.sql import TRUNCATE_GROUPS_TABLE_SQL
    from posthog.models.performance.sql import TRUNCATE_PERFORMANCE_EVENTS_TABLE_SQL
    from posthog.models.person.sql import (
        TRUNCATE_PERSON_DISTINCT_ID2_TABLE_SQL,
        TRUNCATE_PERSON_DISTINCT_ID_OVERRIDES_TABLE_SQL,
        TRUNCATE_PERSON_DISTINCT_ID_TABLE_SQL,
        TRUNCATE_PERSON_STATIC_COHORT_TABLE_SQL,
        TRUNCATE_PERSON_TABLE_SQL,
    )
    from posthog.models.raw_sessions.sql import TRUNCATE_RAW_SESSIONS_TABLE_SQL
    from posthog.models.sessions.sql import TRUNCATE_SESSIONS_TABLE_SQL
    from posthog.session_recordings.sql.session_recording_event_sql import (
        TRUNCATE_SESSION_RECORDING_EVENTS_TABLE_SQL,
    )

    # REMEMBER TO ADD ANY NEW CLICKHOUSE TABLES TO THIS ARRAY!
    TABLES_TO_CREATE_DROP: list[str] = [
        TRUNCATE_EVENTS_TABLE_SQL(),
        TRUNCATE_EVENTS_RECENT_TABLE_SQL(),
        TRUNCATE_PERSON_TABLE_SQL,
        TRUNCATE_PERSON_DISTINCT_ID_TABLE_SQL,
        TRUNCATE_PERSON_DISTINCT_ID2_TABLE_SQL,
        TRUNCATE_PERSON_DISTINCT_ID_OVERRIDES_TABLE_SQL,
        TRUNCATE_PERSON_STATIC_COHORT_TABLE_SQL,
        TRUNCATE_ERROR_TRACKING_ISSUE_FINGERPRINT_OVERRIDES_TABLE_SQL,
        TRUNCATE_SESSION_RECORDING_EVENTS_TABLE_SQL(),
        TRUNCATE_PLUGIN_LOG_ENTRIES_TABLE_SQL,
        TRUNCATE_COHORTPEOPLE_TABLE_SQL,
        TRUNCATE_DEAD_LETTER_QUEUE_TABLE_SQL,
        TRUNCATE_GROUPS_TABLE_SQL,
        TRUNCATE_APP_METRICS_TABLE_SQL,
        TRUNCATE_PERFORMANCE_EVENTS_TABLE_SQL,
        TRUNCATE_CHANNEL_DEFINITION_TABLE_SQL,
        TRUNCATE_EXCHANGE_RATE_TABLE_SQL(),
        TRUNCATE_SESSIONS_TABLE_SQL(),
        TRUNCATE_RAW_SESSIONS_TABLE_SQL(),
        TRUNCATE_HEATMAPS_TABLE_SQL(),
        TRUNCATE_PG_EMBEDDINGS_TABLE_SQL(),
    ]

    # Drop created Kafka tables because some tests don't expect it.
    if settings.IN_EVAL_TESTING:
        kafka_tables = sync_execute(
            f"""
            SELECT name
            FROM system.tables
            WHERE database = '{settings.CLICKHOUSE_DATABASE}' AND name LIKE 'kafka_%'
            """,
        )
        # Using `ON CLUSTER` takes x20 more time to drop the tables: https://github.com/ClickHouse/ClickHouse/issues/15473.
        TABLES_TO_CREATE_DROP += [f"DROP TABLE {table[0]}" for table in kafka_tables]

    run_clickhouse_statement_in_parallel(TABLES_TO_CREATE_DROP)

    from posthog.clickhouse.schema import (
        CREATE_DATA_QUERIES,
    )

    run_clickhouse_statement_in_parallel(list(CREATE_DATA_QUERIES))


@pytest.fixture(scope="package")
def django_db_setup(django_db_setup, django_db_keepdb):
    database = Database(
        settings.CLICKHOUSE_DATABASE,
        db_url=settings.CLICKHOUSE_HTTP_URL,
        username=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        cluster=settings.CLICKHOUSE_CLUSTER,
        verify_ssl_cert=settings.CLICKHOUSE_VERIFY,
        randomize_replica_paths=True,
    )

    if not django_db_keepdb:
        try:
            database.drop_database()
        except:
            pass

    database.create_database()  # Create database if it doesn't exist
    create_clickhouse_tables()

    yield

    if django_db_keepdb:
        # Reset ClickHouse data, unless we're running AI evals, where we want to keep the DB between runs
        if not settings.IN_EVAL_TESTING:
            reset_clickhouse_tables()
    else:
        database.drop_database()


@pytest.fixture
def base_test_mixin_fixture():
    kls = PostHogTestCase()
    kls.setUp()
    kls.setUpTestData()

    return kls


@pytest.fixture
def team(base_test_mixin_fixture):
    return base_test_mixin_fixture.team


@pytest.fixture
def user(base_test_mixin_fixture):
    return base_test_mixin_fixture.user


# :TRICKY: Integrate syrupy with unittest test cases
@pytest.fixture
def unittest_snapshot(request, snapshot):
    request.cls.snapshot = snapshot


@pytest.fixture
def cache():
    from django.core.cache import cache as django_cache

    django_cache.clear()

    yield django_cache

    django_cache.clear()


@pytest.fixture(scope="package", autouse=True)
def load_hog_function_templates(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        from posthog.api.test.test_hog_function_templates import MOCK_NODE_TEMPLATES

        with patch(
            "posthog.management.commands.sync_hog_function_templates.get_hog_function_templates"
        ) as mock_get_templates:
            mock_get_templates.return_value.status_code = 200
            mock_get_templates.return_value.json.return_value = MOCK_NODE_TEMPLATES
            from django.core.management import call_command

            call_command("sync_hog_function_templates")
