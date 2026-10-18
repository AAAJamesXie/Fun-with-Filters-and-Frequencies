"""Real-array tests for unsharp masking and its single-kernel equivalent."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np


class SharpenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = None
        path = Path(__file__).with_name('sharpen.py')
        if path.exists():
            spec = importlib.util.spec_from_file_location('sharpen', path)
            cls.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.module)

    def implementation(self):
        self.assertIsNotNone(self.module, 'Unsharp masking implementation is missing.')
        return self.module

    def test_single_kernel_matches_two_step_on_rgb_and_borders(self):
        image = np.random.default_rng(671).random((19, 21, 3))
        m = self.implementation()
        for alpha in (.5, 1., 2.):
            result = m.unsharp_mask(image, 1.5, alpha)
            np.testing.assert_allclose(result['sharpened'], result['single'], atol=1e-14, rtol=1e-12)
            self.assertEqual(result['sharpened'].shape, image.shape)

    def test_zero_amount_returns_original(self):
        image = np.random.default_rng(2).random((9, 11))
        result = self.implementation().unsharp_mask(image, 1., 0.)
        np.testing.assert_array_equal(result['sharpened'], image)
        np.testing.assert_allclose(result['single'], image, atol=1e-15)

    def test_constant_color_is_preserved_without_channel_mixing(self):
        image = np.broadcast_to([.2, .5, .8], (13, 15, 3)).copy()
        result = self.implementation().unsharp_mask(image, 2., 2.)
        np.testing.assert_allclose(result['sharpened'], image, atol=1e-14)
        np.testing.assert_allclose(result['high'], 0., atol=1e-14)

    def test_high_frequency_is_signed_and_overshoot_is_not_clipped(self):
        image = np.zeros((15, 15)); image[7, 7] = 1.
        result = self.implementation().unsharp_mask(image, 1., 1.)
        self.assertGreater(result['high'].max(), 0.)
        self.assertLess(result['high'].min(), 0.)
        self.assertGreater(result['sharpened'].max(), 1.)
        self.assertLess(result['sharpened'].min(), 0.)

    def test_combined_kernel_has_unit_sum(self):
        result = self.implementation().unsharp_mask(np.eye(15), 1.5, 1.5)
        self.assertAlmostEqual(float(result['kernel'].sum()), 1., places=13)

    def test_invalid_parameters_are_rejected(self):
        m = self.implementation()
        for sigma, alpha in [(0., 1.), (-1., 1.), (1., -1.), (float('nan'), 1.), (1., float('inf'))]:
            with self.assertRaises(ValueError):
                m.unsharp_mask(np.ones((5, 5)), sigma, alpha)


if __name__ == '__main__':
    unittest.main()
