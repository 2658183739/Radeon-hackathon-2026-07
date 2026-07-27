import unittest

from parcel_sorter.mobile_cradle import discover_mobile_v_cradle_geoms


class _Geom:
    def __init__(self, index: int, name: str = "") -> None:
        self.idx = index
        self.name = name


class _Link:
    def __init__(self, name: str, geoms: list[_Geom]) -> None:
        self.name = name
        self.geoms = geoms


class MobileCradleDiscoveryTests(unittest.TestCase):
    def test_discovers_two_named_cradle_geometries(self) -> None:
        robot = type(
            "Robot",
            (),
            {
                "links": [
                    _Link(
                        "tool",
                        [
                            _Geom(4, "mobile_right_v_cradle_left_collision"),
                            _Geom(5, "mobile_right_v_cradle_right_collision"),
                        ],
                    )
                ]
            },
        )()
        self.assertEqual(discover_mobile_v_cradle_geoms(robot), frozenset({4, 5}))

    def test_uses_audited_append_order_when_names_are_missing(self) -> None:
        robot = type(
            "Robot",
            (),
            {"links": [_Link("panda1_gripper", [_Geom(index) for index in range(6)])]},
        )()
        self.assertEqual(discover_mobile_v_cradle_geoms(robot), frozenset({4, 5}))


if __name__ == "__main__":
    unittest.main()
