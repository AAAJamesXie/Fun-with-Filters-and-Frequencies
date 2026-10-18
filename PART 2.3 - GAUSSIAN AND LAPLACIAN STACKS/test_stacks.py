"""Real-array tests for full-resolution stacks and band-wise blending."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np


class StackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = None
        path = Path(__file__).with_name('stacks.py')
        if path.exists():
            spec = importlib.util.spec_from_file_location('stacks', path)
            cls.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.module)

    def implementation(self):
        self.assertIsNotNone(self.module, 'Stack implementation is missing.')
        return self.module

    def test_all_gaussian_levels_keep_original_dimensions(self):
        image = np.random.default_rng(671).random((17, 19, 3))
        result = self.implementation().gaussian_stack(image, (0, 1, 2, 4))
        self.assertEqual(result.shape, (4, 17, 19, 3))
        np.testing.assert_array_equal(result[0], image)

    def test_laplacian_sum_recovers_odd_sized_rgb_image(self):
        m = self.implementation()
        image = np.random.default_rng(2).random((17, 19, 3))
        gaussian = m.gaussian_stack(image, (0, 1, 2, 4))
        laplacian = m.laplacian_stack(gaussian)
        np.testing.assert_allclose(laplacian.sum(axis=0), image, atol=1e-14)
        np.testing.assert_array_equal(laplacian[-1], gaussian[-1])

    def test_constant_image_has_only_coarse_residual(self):
        m = self.implementation()
        laplacian = m.laplacian_stack(m.gaussian_stack(np.full((21, 23), .7), (0, 1, 2, 4)))
        np.testing.assert_allclose(laplacian[:-1], 0, atol=1e-14)
        np.testing.assert_allclose(laplacian[-1], .7, atol=1e-14)

    def test_gaussian_removes_impulse_peak_progressively(self):
        image = np.zeros((41, 43)); image[20, 21] = 1.
        stack = self.implementation().gaussian_stack(image, (0, 1, 2, 4))
        self.assertTrue(np.all(np.diff(stack[:, 20, 21]) < 0))

    def test_mask_extremes_select_each_input(self):
        m = self.implementation(); rng = np.random.default_rng(3)
        a, b = rng.random((15, 17, 3)), rng.random((15, 17, 3))
        la = m.laplacian_stack(m.gaussian_stack(a, (0, 1, 2)))
        lb = m.laplacian_stack(m.gaussian_stack(b, (0, 1, 2)))
        np.testing.assert_allclose(m.blend_stacks(la, lb, np.ones((3, 15, 17)))['image'], a, atol=1e-14)
        np.testing.assert_allclose(m.blend_stacks(la, lb, np.zeros((3, 15, 17)))['image'], b, atol=1e-14)

    def test_identical_inputs_are_unchanged_by_spatial_masks(self):
        m = self.implementation(); rng = np.random.default_rng(4)
        image = rng.random((15, 17, 3))
        lap = m.laplacian_stack(m.gaussian_stack(image, (0, 1, 2, 4)))
        masks = m.gaussian_stack((np.indices((15, 17))[1] < 8).astype(float), (1, 2, 4, 8))
        result = m.blend_stacks(lap, lap, masks)
        np.testing.assert_allclose(result['image'], image, atol=1e-14)
        np.testing.assert_allclose(result['left'] + result['right'], result['image'], atol=1e-14)

    def test_signed_band_is_not_clipped(self):
        m = self.implementation()
        image = np.zeros((15, 17)); image[7, 8] = 1.
        lap = m.laplacian_stack(m.gaussian_stack(image, (0, 1, 2)))
        self.assertLess(lap[0].min(), 0)
        self.assertGreater(lap[0].max(), 0)

    def test_invalid_scale_order_or_mask_is_rejected(self):
        m = self.implementation()
        for sigmas in ((0, 2, 1), (0, 1, 1), (-1, 2), (0, float('nan'))):
            with self.assertRaises(ValueError): m.gaussian_stack(np.ones((9, 9)), sigmas)
        with self.assertRaises(ValueError): m.blend_stacks(np.ones((3, 9, 9)), np.ones((3, 9, 9)), np.full((3, 9, 9), 2.))


if __name__ == '__main__':
    unittest.main()
