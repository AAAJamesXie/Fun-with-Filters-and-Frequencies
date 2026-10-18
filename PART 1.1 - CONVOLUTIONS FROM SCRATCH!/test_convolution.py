"""Real-array unit tests: flipping, centering, boundaries and signed outputs."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np
from scipy.signal import convolve2d


class ConvolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).with_name('convolution.py')
        cls.module = None
        if path.exists():
            spec = importlib.util.spec_from_file_location('convolution', path)
            cls.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.module)

    def compare(self, image, kernel):
        self.assertIsNotNone(self.module, 'The handwritten convolution module is missing.')
        expected = convolve2d(image, kernel, mode='same', boundary='fill', fillvalue=0)
        for name in ('convolve_four_loops', 'convolve_two_loops'):
            with self.subTest(implementation=name, kernel_shape=kernel.shape):
                actual = getattr(self.module, name)(image, kernel)
                self.assertEqual(actual.shape, image.shape)
                np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)

    def test_asymmetric_kernel_requires_flipping(self):
        self.compare(np.arange(20).reshape(4, 5), np.array([[1, 2, 4], [8, 16, 32], [64, 128, 256]]))

    def test_even_kernel_centering_and_signed_derivatives(self):
        image = np.arange(20, dtype=np.uint8).reshape(4, 5)
        for kernel in (np.array([[1, -1]]), np.array([[1], [-1]]), np.array([[1, 2], [3, 4]])):
            self.compare(image, kernel)

    def test_zero_padding_with_kernel_larger_than_image(self):
        self.compare(np.ones((2, 3)), np.ones((9, 9)) / 81)

    def test_impulse_at_boundary(self):
        image = np.zeros((5, 6))
        image[0, 0] = 1
        self.compare(image, np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]))

    def test_identity_and_zero_kernel(self):
        image = np.random.default_rng(671).normal(size=(6, 7))
        self.compare(image, np.ones((1, 1)))
        self.compare(image, np.zeros((3, 3)))


if __name__ == '__main__':
    unittest.main()
