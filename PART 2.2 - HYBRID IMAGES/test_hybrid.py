"""Real-array tests for alignment, filtering, color variants and spectra."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np


class HybridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = None
        path = Path(__file__).with_name('hybrid.py')
        if path.exists():
            spec = importlib.util.spec_from_file_location('hybrid', path)
            cls.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.module)

    def implementation(self):
        self.assertIsNotNone(self.module, 'Hybrid implementation is missing.')
        return self.module

    def test_similarity_recovers_scale_rotation_and_translation(self):
        source = np.array([[1., 2.], [5., 2.]])
        target = np.array([[10., 20.], [10., 28.]])
        matrix = self.implementation().similarity_matrix(source, target)
        np.testing.assert_allclose(np.c_[source, np.ones(2)] @ matrix.T, target, atol=1e-14)
        np.testing.assert_allclose(matrix[:, :2], [[0, -2], [2, 0]], atol=1e-14)

    def test_identity_warp_preserves_rgb(self):
        image = np.random.default_rng(671).random((8, 9, 3))
        result, valid = self.implementation().warp_image(image, np.array([[1., 0., 0.], [0., 1., 0.]]), (9, 8))
        np.testing.assert_array_equal(result, image)
        self.assertTrue(valid.all())

    def test_common_rectangle_excludes_invalid_pixels(self):
        mask = np.zeros((6, 8), dtype=bool); mask[1:5, 2:7] = True; mask[0, 3:5] = True
        self.assertEqual(self.implementation().largest_rectangle(mask), (2, 1, 7, 5))

    def test_constant_image_has_zero_high_frequency(self):
        image = np.broadcast_to([.2, .5, .8], (21, 23, 3)).copy()
        result = self.implementation().make_hybrid(image, image, 2., 3., 1., 'both_color')
        np.testing.assert_allclose(result['low'], image, atol=1e-14)
        np.testing.assert_allclose(result['high'], 0., atol=1e-14)

    def test_matching_bands_reconstruct_same_input(self):
        image = np.random.default_rng(2).random((19, 21, 3))
        result = self.implementation().make_hybrid(image, image, 2., 2., 1., 'both_color')
        np.testing.assert_allclose(result['hybrid'], image, atol=1e-14)
        self.assertLess(result['high'].min(), 0.)
        self.assertGreater(result['high'].max(), 0.)

    def test_grayscale_variant_has_equal_channels(self):
        rng = np.random.default_rng(3)
        result = self.implementation().make_hybrid(rng.random((17, 18, 3)), rng.random((17, 18, 3)), 2., 1., 1., 'gray')
        np.testing.assert_array_equal(result['hybrid'][:, :, 0], result['hybrid'][:, :, 1])
        np.testing.assert_array_equal(result['hybrid'][:, :, 1], result['hybrid'][:, :, 2])

    def test_constant_spectrum_peak_is_centered(self):
        spectrum = self.implementation().log_spectrum(np.ones((16, 18)))
        self.assertEqual(np.unravel_index(np.argmax(spectrum), spectrum.shape), (8, 9))
        self.assertTrue(np.isfinite(spectrum).all())

    def test_invalid_parameters_and_coincident_landmarks(self):
        m = self.implementation()
        with self.assertRaises(ValueError): m.similarity_matrix([[0, 0], [0, 0]], [[0, 0], [1, 1]])
        with self.assertRaises(ValueError): m.gaussian_blur(np.ones((8, 8)), 0.)
        with self.assertRaises(ValueError): m.largest_rectangle(np.zeros((3, 4), dtype=bool))


if __name__ == '__main__':
    unittest.main()
