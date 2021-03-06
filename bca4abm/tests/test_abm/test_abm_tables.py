import os.path

import numpy.testing as npt
import pandas as pd
import pandas.util.testing as pdt
import pytest

import orca
from activitysim.core import inject
from activitysim.core import config


# orca injectables complicate matters because the decorators are executed at module load time
# and since py.test collects modules and loads them at the start of a run
# if a test method does something that has a lasting side-effect, then that side effect
# will carry over not just to subsequent test functions, but to subsequently called modules
# for instance, columns added with add_column will remain attached to orca tables
# pytest-xdist allows us to run py.test with the --boxed option which runs every function
# with a brand new python interpreter
# py.test --boxed --cov bca4abm

# Also note that the following import statement has the side-effect of registering injectables:
from bca4abm import bca4abm as bca

from bca4abm.util.misc import expect_columns, missing_columns, extra_columns, mapped_columns


@pytest.fixture(scope="module", autouse=True)
def inject_default_directories(request):

    parent_dir = os.path.dirname(__file__)
    inject.add_injectable("configs_dir", os.path.join(parent_dir, 'configs'))
    inject.add_injectable("data_dir", os.path.join(parent_dir, 'data'))
    inject.add_injectable("output_dir", os.path.join(parent_dir, 'output'))

    request.addfinalizer(orca.clear_cache)


def test_read_persons_table():

    table_settings = config.read_model_settings('tables.yaml')
    assert table_settings.get('persons') == 'persons.csv'

    # expect all of and only the columns specified by persons_column_map values
    persons = inject.get_table('persons').to_frame()
    assert expect_columns(persons,
                          table_settings['persons_column_map'].values())

    assert persons.shape[0] == 27


def test_read_households_table():

    table_settings = config.read_model_settings('tables.yaml')

    households = inject.get_table('households').to_frame()
    assert not missing_columns(households,
                               table_settings['base_households_column_map'].values())

    assert not missing_columns(households,
                               table_settings['build_households_column_map'].values())

    assert households.shape[0] == 9


def test_persons_merged_table():

    persons_merged = inject.get_table('persons_merged').to_frame()
    assert 'person_gender' in persons_merged.columns
    assert 'hh_income' in persons_merged.columns

    persons = inject.get_table('persons').to_frame()
    assert (persons_merged.person_type == persons.person_type).all()

    assert persons_merged.shape[0] == 27


def test_read_base_trips_table():

    table_settings = config.read_model_settings('tables.yaml')

    assert table_settings.get('basetrips') == 'basetrips_normal.csv'

    trips = inject.get_table('base_trips').to_frame()

    # expect all of and only the columns specified by column_map values
    raw_columns = \
        mapped_columns(
            table_settings['basetrips_column_map'],
            table_settings['basetrips_buildlos_column_map']) + ['build', 'base', 'person_id']

    assert expect_columns(trips, raw_columns)

    assert trips.shape[0] == 123


def test_read_build_trips_table():

    table_settings = config.read_model_settings('tables.yaml')
    assert table_settings.get('buildtrips') == 'buildtrips_normal.csv'

    trips = inject.get_table('build_trips').to_frame()

    # expect all of and only the columns specified by persons_column_map values
    raw_columns = \
        mapped_columns(
            table_settings['buildtrips_column_map'],
            table_settings['buildtrips_baselos_column_map']) + ['build', 'base', 'person_id']

    assert expect_columns(trips, raw_columns)

    assert trips.shape[0] == 127


def test_disaggregate_trips_table():

    trips = inject.get_table('disaggregate_trips').to_frame()
    assert 'build_auto_time' in trips.columns
    assert 'base_auto_time' in trips.columns

    assert trips.shape[0] == 250


def test_trips_with_demographics_table():

    trips = inject.get_table('trips_with_demographics').to_frame()
    assert 'build_auto_time' in trips.columns
    assert 'base_auto_time' in trips.columns
    assert 'person_age' in trips.columns
    assert 'hh_income' in trips.columns

    assert trips.shape[0] == 250
