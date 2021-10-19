import unittest
from image_pull_size import infer_ref


class TestApp(unittest.TestCase):

    def test_infer_ref(self):
        test_cases = [
            ("python:3.8", "docker.io/library/python:3.8"),
            ("library/python:3.8", "docker.io/library/python:3.8"),
            ("docker.io/library/python:3.8", "docker.io/library/python:3.8"),
            ("python:latest", "docker.io/library/python:latest"),
            ("python:3.8@sha256:1217b63826ce00974b4464e9dc088262ef54abd8a4ec66be2b76be971a17580a", "docker.io/library/python:3.8@sha256:1217b63826ce00974b4464e9dc088262ef54abd8a4ec66be2b76be971a17580a"),
        ]

        for tc in test_cases:
            self.assertEqual(infer_ref(tc[0]), tc[1])


if __name__ == "__main__":
    unittest.main()
