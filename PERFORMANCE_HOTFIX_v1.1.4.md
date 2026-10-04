# V-CAPAT PRO v1.1.4 Windows performance hotfix

## Why this release exists

The Windows release gate correctly rejected `medium_foggy_figure8` when the measured pipeline rate fell below the SIH target of 20 FPS. The threshold has **not** been relaxed. The processing path itself was optimized.

## Optimizations

- Gaussian image noise uses deterministic `cv2.randn` plus saturating `cv2.add`, avoiding a full-frame float64 NumPy normal allocation every frame.
- The OpenCV random generator is reseeded from the scenario `numpy.random.Generator`, preserving repeatable seeded runs.
- Salt-and-pepper simulation now samples only the requested impulse locations instead of allocating a full-frame random float mask.
- Adaptive thresholding uses an 8-bit histogram median plus `cv2.meanStdDev` and `cv2.threshold`.
- Top-hat thresholding uses `cv2.meanStdDev` and cached morphology kernels.
- Auto detector scene statistics use `cv2.meanStdDev` rather than a NumPy whole-frame standard deviation.

## Integrity

The functional performance assertion remains `average_processing_fps >= 20` for both clear circular and medium fog/figure-eight regression scenarios. No test threshold or PS requirement was reduced to make the release pass.
