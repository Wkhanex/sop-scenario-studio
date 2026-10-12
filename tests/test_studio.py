import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from sop_studio.builder import build_world
from sop_studio.cli import main
from sop_studio.schema import ScenarioError, timestamp, validate_trace, validate_world
from sop_studio.simulation import simulate

ROOT = Path(__file__).resolve().parents[1]
def fixture(name='world.json'): return json.loads((ROOT/'examples'/name).read_text())

class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_good_trace_moves_through_the_workflow(self):
        result = simulate(fixture(), fixture('good-trace.json'))
        self.assertEqual((3, 0, {'HELP-41': 'scheduled'}), (result['accepted'], result['rejected'], result['final_states']))
        self.assertEqual(['SLOT-7'], result['decisions'][-1]['used_evidence_ids'])

    def test_bad_trace_preserves_state_for_rejected_writes(self):
        result = simulate(fixture(), fixture('bad-trace.json'))
        self.assertEqual((2, 3, {'HELP-41': 'approved'}), (result['accepted'], result['rejected'], result['final_states']))
        self.assertTrue(all(d['state_before'] == d['state_after'] for d in result['decisions'] if not d['accepted']))

    def test_simulation_does_not_mutate_world_or_trace(self):
        world, trace = fixture(), fixture('good-trace.json')
        original = copy.deepcopy((world, trace))
        simulate(world, trace)
        self.assertEqual(original, (world, trace))

    def test_wrong_role_blocks_manager_approval(self):
        trace = fixture('good-trace.json')
        trace['events'][1]['actor_id'] = 'OPS'
        result = simulate(fixture(), trace)
        self.assertFalse(result['decisions'][1]['accepted'])
        self.assertIn('actor requires role manager', result['decisions'][1]['reasons'])

    def test_same_evidence_type_with_wrong_body_is_insufficient(self):
        world = fixture()
        world['records'][2]['body']['request_id'] = 'OTHER'
        result = simulate(world, fixture('good-trace.json'))
        self.assertFalse(result['decisions'][-1]['accepted'])

    def test_evidence_author_role_is_enforced(self):
        world = fixture()
        world['records'][2]['actor_id'] = 'OPS'
        self.assertFalse(simulate(world, fixture('good-trace.json'))['decisions'][-1]['accepted'])

    def test_evidence_boolean_is_not_equal_to_integer(self):
        world = fixture()
        world['records'][2]['body']['approved'] = 1
        self.assertFalse(simulate(world, fixture('good-trace.json'))['decisions'][-1]['accepted'])

    def test_missing_prerequisite_blocks_action(self):
        world = fixture()
        world['workflow']['initial_states']['HELP-41'] = 'approved'
        trace = {'events': [fixture('good-trace.json')['events'][-1]]}
        result = simulate(world, trace)
        self.assertIn('missing earlier accepted action: approve', result['decisions'][0]['reasons'])

    def test_deadline_boundary_and_late_action(self):
        world = fixture()
        world['workflow']['transitions'][2]['deadline'] = '2026-09-14T09:37:00+01:00'
        trace = fixture('good-trace.json')
        self.assertTrue(simulate(world, trace)['decisions'][-1]['accepted'])
        trace['events'][-1]['at'] = '2026-09-14T09:37:01+01:00'
        self.assertFalse(simulate(world, trace)['decisions'][-1]['accepted'])

    def test_offsets_compare_as_instants(self):
        self.assertEqual(timestamp('2026-09-14T09:30:00+01:00'), timestamp('2026-09-14T08:30:00Z'))
        world = fixture()
        world['records'][2]['at'] = '2026-09-14T10:25:00+02:00'
        validate_world(world)

    def test_future_evidence_is_rejected_by_utc_instant(self):
        world = fixture()
        world['records'][2]['at'] = '2026-09-14T09:25:00Z'
        with self.assertRaisesRegex(ScenarioError, 'after the world clock'): validate_world(world)

    def test_naive_and_invalid_timestamps_are_rejected(self):
        for value in ('2026-09-14T09:30:00', '2026-02-30T00:00:00Z', 'tomorrow', None):
            with self.assertRaises(ScenarioError): timestamp(value)

    def test_duplicate_record_and_actor_ids_are_rejected(self):
        for collection in ('actors', 'records', 'clauses'):
            world = fixture()
            world[collection].append(copy.deepcopy(world[collection][0]))
            with self.assertRaisesRegex(ScenarioError, 'duplicate'): validate_world(world)

    def test_dangling_actor_and_record_references_are_rejected(self):
        for field, value in (('actor_id', 'MISSING'), ('refs', ['MISSING'])):
            world = fixture()
            world['records'][0][field] = value
            with self.assertRaises(ScenarioError): validate_world(world)

    def test_declared_absence_must_remain_absent(self):
        world = fixture()
        world['absences'][0]['service'] = 'tickets'
        world['absences'][0]['type'] = 'helpdesk-slot'
        with self.assertRaisesRegex(ScenarioError, 'declared absence'): validate_world(world)

    def test_unknown_clause_and_duplicate_transition_are_rejected(self):
        world = fixture()
        world['workflow']['transitions'][0]['clause'] = '99.9'
        with self.assertRaises(ScenarioError): validate_world(world)
        world = fixture()
        world['workflow']['transitions'].append(world['workflow']['transitions'][0])
        with self.assertRaises(ScenarioError): validate_world(world)

    def test_trace_requires_known_evidence_and_unique_ids(self):
        for change in ('unknown', 'duplicate', 'shape'):
            trace = fixture('good-trace.json')
            trace['events'][0]['evidence_ids'] = ['MISSING'] if change == 'unknown' else ['CONTACT-12', 'CONTACT-12'] if change == 'duplicate' else [{}]
            with self.assertRaises(ScenarioError): validate_trace(trace, fixture())

    def test_trace_order_and_clock_are_enforced(self):
        for time in ('2026-09-14T09:29:00+01:00', '2026-09-14T09:30:00+01:00'):
            trace = fixture('good-trace.json')
            trace['events'][1]['at'] = time
            with self.assertRaises(ScenarioError): validate_trace(trace, fixture())

    def test_unknown_action_is_rejected_without_a_state_change(self):
        trace = fixture('good-trace.json')
        trace['events'][-1]['action'] = 'delete_everything'
        self.assertEqual('approved', simulate(fixture(), trace)['final_states']['HELP-41'])

    def test_authorized_helpdesk_assignment_can_follow_scheduling(self):
        trace = fixture('good-trace.json')
        trace['events'].append({'id': 'E4', 'action': 'assign', 'actor_id': 'HELPDESK', 'target_id': 'HELP-41',
                                'at': '2026-09-14T09:40:00+01:00', 'evidence_ids': []})
        self.assertEqual('assigned', simulate(fixture(), trace)['final_states']['HELP-41'])

    def test_build_preserves_records_and_counts(self):
        result = build_world(fixture(), self.root/'pack')
        self.assertEqual(3, result['budget']['records'])
        self.assertEqual(fixture(), json.loads((self.root/'pack/world.json').read_text()))
        self.assertEqual(2, len(json.loads((self.root/'pack/services/tickets.json').read_text())['records']))
        hashes = json.loads((self.root/'pack/checksums.json').read_text())
        self.assertTrue(all(hashlib.sha256((self.root/'pack'/p).read_bytes()).hexdigest() == h for p, h in hashes.items()))

    def test_scenario_zip_is_reproducible(self):
        build_world(fixture(), self.root/'a')
        build_world(fixture(), self.root/'b')
        self.assertEqual((self.root/'a/scenario.zip').read_bytes(), (self.root/'b/scenario.zip').read_bytes())

    def test_invalid_world_and_existing_output_are_not_overwritten(self):
        world = fixture()
        world['records'][0]['service'] = '../outside'
        with self.assertRaises(ScenarioError): build_world(world, self.root/'bad')
        self.assertFalse((self.root/'bad').exists())
        build_world(fixture(), self.root/'pack')
        with self.assertRaises(ScenarioError): build_world(fixture(), self.root/'pack')

    def test_cli_exit_codes(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(0, main(['validate', str(ROOT/'examples/world.json')]))
            self.assertEqual(0, main(['simulate', str(ROOT/'examples/world.json'), str(ROOT/'examples/good-trace.json')]))
            self.assertEqual(1, main(['simulate', str(ROOT/'examples/world.json'), str(ROOT/'examples/bad-trace.json')]))
            self.assertEqual(2, main(['validate', str(self.root/'missing.json')]))

if __name__ == '__main__': unittest.main()
