"""Real-array tests for Gaussian/DoG filtering and manual gradient direction."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np


class DogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = None
        path = Path(__file__).with_name('dog.py')
        if path.exists():
            spec = importlib.util.spec_from_file_location('dog', path)
            cls.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.module)

    def implementation(self):
        self.assertIsNotNone(self.module, 'DoG implementation is missing.')
        return self.module

    def test_gaussian_is_normalized_symmetric_and_positive(self):
        g = self.implementation().gaussian_kernel(2.)
        self.assertEqual(g.shape, (13, 13))
        self.assertAlmostEqual(float(g.sum()), 1., places=14)
        self.assertTrue((g > 0).all())
        np.testing.assert_allclose(g, g[::-1, ::-1], atol=1e-15)

    def test_dog_filters_have_full_support_and_zero_dc(self):
        g, kx, ky = self.implementation().dog_kernels(2.)
        self.assertEqual(kx.shape, (13, 14))
        self.assertEqual(ky.shape, (14, 13))
        self.assertAlmostEqual(float(kx.sum()), 0., places=14)
        self.assertAlmostEqual(float(ky.sum()), 0., places=14)
        np.testing.assert_allclose(kx.T, ky, atol=1e-15)

    def test_two_routes_agree_in_valid_interior(self):
        m = self.implementation()
        image = np.random.default_rng(671).random((51, 57))
        result = m.filter_routes(image, 2.)
        margin = result['margin']
        for axis in ('x', 'y'):
            np.testing.assert_allclose(result['sequential_' + axis][margin:-margin, margin:-margin],
                                       result['direct_' + axis][margin:-margin, margin:-margin],
                                       rtol=1e-12, atol=1e-14)

    def test_constant_image_has_zero_gradient(self):
        result = self.implementation().filter_routes(np.full((25, 27), .7), 1.)
        for name in ('sequential_x', 'sequential_y', 'direct_x', 'direct_y'):
            np.testing.assert_allclose(result[name], 0., atol=1e-14)

    def test_manual_angles_axes_quadrants_and_zero(self):
        m = self.implementation()
        dx = np.array([[1., 1., 0., -1., -1., -1., 0., 1., 0.]])
        dy = np.array([[0., 1., 1., 1., 0., -1., -1., -1., 0.]])
        expected = np.array([[0., 1., 2., 3., 4., 5., 6., 7., 0.]]) * np.pi / 4
        np.testing.assert_allclose(m.manual_orientation(dx, dy), expected, atol=1e-14)

    def test_manual_angles_known_non_diagonal_slopes(self):
        dx = np.array([[2., 1., np.sqrt(3.), -2.]])
        dy = np.array([[1., 2., 1., -1.]])
        expected = [[.4636476090008061, 1.1071487177940904, np.pi / 6, 3.6052402625905993]]
        np.testing.assert_allclose(self.implementation().manual_orientation(dx, dy), expected, atol=1e-14)

    def test_hsv_cardinal_colors_and_zero_strength(self):
        m = self.implementation()
        theta = np.array([[0., 2 * np.pi / 3, 4 * np.pi / 3, 0.]])
        strength = np.array([[1., 1., 1., 0.]])
        rgb = m.orientation_rgb(theta, strength, 1.)
        np.testing.assert_allclose(rgb, [[[1., 0., 0.], [0., 1., 0.], [0., 0., 1.], [0., 0., 0.]]], atol=1e-14)


if __name__ == '__main__':
    unittest.main()
