"""Real-array unit tests for irregular masks and the reused stack pipeline."""
import unittest
import numpy as np
from blending import polygon_mask, step_mask, multiresolution_blend, color_inputs


class BlendingTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(671)
        self.a = self.rng.random((31, 43, 3))
        self.b = self.rng.random((31, 43, 3))

    def test_polygon_selects_only_inside(self):
        mask = polygon_mask((31, 43), [(8, 7), (33, 7), (20, 25)])
        self.assertEqual(mask[12, 20], 1)
        self.assertEqual(mask[0, 0], 0)
        self.assertEqual(set(np.unique(mask)), {0., 1.})

    def test_step_selects_left(self):
        mask = step_mask((31, 43), .4)
        self.assertTrue((mask[:, :17] == 1).all())
        self.assertTrue((mask[:, 17:] == 0).all())

    def test_identical_inputs_reconstruct_on_irregular_mask(self):
        mask = polygon_mask((31, 43), [(3, 3), (38, 10), (15, 28)])
        result = multiresolution_blend(self.a, self.a, mask)
        np.testing.assert_allclose(result['image'], self.a, atol=5e-15)
        self.assertEqual(result['bands'].shape, (6, 31, 43, 3))

    def test_full_masks_select_correct_source(self):
        for value, expected in [(1., self.a), (0., self.b)]:
            result = multiresolution_blend(self.a, self.b, np.full((31, 43), value))
            np.testing.assert_allclose(result['image'], expected, atol=5e-15)

    def test_weighted_contributions_sum_without_clipping(self):
        result = multiresolution_blend(self.a, self.b, step_mask((31, 43)))
        np.testing.assert_allclose(result['left'] + result['right'], result['image'], atol=1e-15)
        np.testing.assert_allclose(result['left_bands'] + result['right_bands'], result['bands'], atol=0)
        self.assertLess(result['left_laplacian'][:-1].min(), 0)

    def test_color_modes_preserve_selected_channels(self):
        for mode in ('gray', 'a_color', 'b_color', 'both_color'):
            a, b = color_inputs(self.a, self.b, mode)
            for actual, original, colorful in [(a, self.a, mode in ('a_color', 'both_color')),
                                                 (b, self.b, mode in ('b_color', 'both_color'))]:
                if colorful:
                    np.testing.assert_array_equal(actual, original)
                else:
                    np.testing.assert_array_equal(actual[..., 0], actual[..., 2])

    def test_channel_independence(self):
        a, b = np.zeros_like(self.a), np.zeros_like(self.b)
        a[..., 0] = self.a[..., 0]
        result = multiresolution_blend(a, b, step_mask((31, 43)))
        np.testing.assert_array_equal(result['image'][..., 1:], 0)

    def test_invalid_inputs_rejected(self):
        for mask in [np.zeros((3, 4)), np.full((31, 43), -1.), np.full((31, 43), np.nan)]:
            with self.assertRaises(ValueError):
                multiresolution_blend(self.a, self.b, mask)
        with self.assertRaises(ValueError):
            polygon_mask((31, 43), [(1, 1), (4, 4)])
        with self.assertRaises(ValueError):
            color_inputs(self.a, self.b, 'invalid')


if __name__ == '__main__':
    unittest.main()
