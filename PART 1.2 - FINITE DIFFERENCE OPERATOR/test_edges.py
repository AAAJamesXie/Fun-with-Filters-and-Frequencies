"""Real-array tests for directional differences, magnitude and binarization."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np


class EdgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = None
        path = Path(__file__).with_name('edges.py')
        if path.exists():
            spec = importlib.util.spec_from_file_location('edges', path)
            cls.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.module)

    def implementation(self):
        self.assertIsNotNone(self.module, 'Finite difference implementation is missing.')
        return self.module

    def test_horizontal_ramp_has_only_horizontal_derivative(self):
        dx, dy, magnitude = self.implementation().gradients(np.array([[0, 2, 4], [0, 2, 4]], dtype=np.uint8))
        np.testing.assert_array_equal(dx, [[0, 2, 2], [0, 2, 2]])
        np.testing.assert_array_equal(dy, np.zeros((2, 3)))
        np.testing.assert_array_equal(magnitude, [[0, 2, 2], [0, 2, 2]])

    def test_vertical_decrease_preserves_negative_values(self):
        dx, dy, magnitude = self.implementation().gradients(np.array([[6, 6], [3, 3], [0, 0]], dtype=np.uint8))
        np.testing.assert_array_equal(dx, np.zeros((3, 2)))
        np.testing.assert_array_equal(dy, [[0, 0], [-3, -3], [-3, -3]])
        np.testing.assert_array_equal(magnitude, [[0, 0], [3, 3], [3, 3]])

    def test_constant_image_has_no_artificial_border(self):
        dx, dy, magnitude = self.implementation().gradients(np.full((4, 5), 0.7))
        for array in (dx, dy, magnitude):
            np.testing.assert_array_equal(array, np.zeros((4, 5)))

    def test_diagonal_gradient_uses_euclidean_magnitude(self):
        dx, dy, magnitude = self.implementation().gradients(np.array([[0., 3.], [4., 7.]]))
        self.assertEqual(dx[1, 1], 3.)
        self.assertEqual(dy[1, 1], 4.)
        self.assertEqual(magnitude[1, 1], 5.)

    def test_threshold_is_strict_and_returns_boolean(self):
        mask = self.implementation().threshold_edges(np.array([[0., 0.1, 0.2, 0.3]]), 0.2)
        self.assertEqual(mask.dtype, np.dtype(bool))
        np.testing.assert_array_equal(mask, [[False, False, False, True]])

    def test_invalid_inputs_are_rejected(self):
        module = self.implementation()
        for array in (np.array([]), np.zeros((2, 2, 3)), np.array([[np.nan]])):
            with self.assertRaises(ValueError):
                module.gradients(array)
        for value in (-0.1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                module.threshold_edges(np.ones((2, 2)), value)


if __name__ == '__main__':
    unittest.main()
