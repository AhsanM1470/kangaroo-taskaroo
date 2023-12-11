"""Unit tests for the Lane model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import Lane

class LaneModelTestCase(TestCase):
    """Unit tests for the Lane model."""
    def setUp(self):
        self.lane = Lane.objects.create(
            lane_name = "New Lane",
            lane_order = 1
        )

        self.lane2 = Lane.objects.create(
            lane_name = "New Lane",
            lane_order = 2
        )
        
    def test_valid_user(self):
        self._assert_lane_is_valid
        
    # Name Tests
    
    def test_lane_name_cannot_be_blank(self):
        self.lane.lane_name = ''
        self._assert_lane_is_invalid
        
    def test_lane_name_can_be_50_characters_long(self):
        self.lane.lane_name ='x' * 50
        self._assert_lane_is_valid
    
    def test_lane_name_cannot_be_over_50_characters_long(self):
        self.lane.name = 'x' * 51
        self._assert_lane_is_invalid

    # check test
    def test_lane_name_non_unique(self):
        self.assertEqual(self.lane.lane_name, self.lane2.lane_name)
        self.assertNotEqual(self.lane.lane_name, "New Lane 2")
        
    def test_lane_name_must_only_contain_alphanumerics(self):
        self.lane.lane_name = 'La-ne1'
        self._assert_lane_is_invalid
        
    # Order Tests
    
    # def test_lane_order_must_be_unique(self):
    #     self.lane.lane_order = 1
    #     self.lane2.lane_order = 1
    #     self._assert_lane_is_invalid

    # fix this test
    # def test_lane_order_cannot_be_blank(self):

    # Lane ID
    
    def test_lane_id_must_be_unique(self):
        self.lane.lane_id = 1
        self.lane2.lane_id = 1
        self._assert_lane_is_invalid
    
    # def test_lane_id_cannot_be_blank(self):

    # Assertions:
    
    def _assert_lane_is_valid(self):
        try:
            self.lane.full_clean()
        except ValidationError:
            self.fail('Test task should be valid')
            
    def _assert_lane_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.lane.full_clean()