import unittest
from htpclient.hashcat_status import HashcatStatus

class TestHashcatStatus(unittest.TestCase):
    def test_hashcat_6_single_device(self):
        line = "STATUS\t3\tSPEED\t11887844\t1000\tEXEC_RUNTIME\t15.870873\tCURKU\t170970511093\tPROGRESS\t2735618289488\t2736891330000\tRECHASH\t0\t1\tRECSALT\t0\t1\tTEMP\t-1\tREJECTED\t0\tUTIL\t100\t"
        status = HashcatStatus(line)
        self.assertTrue(status.is_valid())
        self.assertEqual(status.status, 3)
        self.assertEqual(status.speed, [[11887844, 1000]])
        self.assertEqual(status.exec_runtime, [15.870873])
        self.assertEqual(status.curku, 170970511093)
        self.assertEqual(status.progress, [2735618289488, 2736891330000])
        self.assertEqual(status.rec_hash, [0, 1])
        self.assertEqual(status.rec_salt, [0, 1])
        self.assertEqual(status.temp, [-1])
        self.assertEqual(status.rejected, 0)
        self.assertEqual(status.util, [100])
        self.assertEqual(status.power, [])
        self.assertEqual(status.unknown_fields, False)

    def test_hashcat_7_single_device(self):
        line = "STATUS\t3\tSPEED\t11887844\t1000\tEXEC_RUNTIME\t15.870873\tCURKU\t170970511093\tPROGRESS\t2735618289488\t2736891330000\tRECHASH\t0\t1\tRECSALT\t0\t1\tTEMP\t-1\tREJECTED\t0\tUTIL\t100\tPOWER\t56\t"
        status = HashcatStatus(line)
        self.assertTrue(status.is_valid())
        self.assertEqual(status.status, 3)
        self.assertEqual(status.speed, [[11887844, 1000]])
        self.assertEqual(status.exec_runtime, [15.870873])
        self.assertEqual(status.curku, 170970511093)
        self.assertEqual(status.progress, [2735618289488, 2736891330000])
        self.assertEqual(status.rec_hash, [0, 1])
        self.assertEqual(status.rec_salt, [0, 1])
        self.assertEqual(status.temp, [-1])
        self.assertEqual(status.rejected, 0)
        self.assertEqual(status.util, [100])
        self.assertEqual(status.power, [56])
        self.assertEqual(status.unknown_fields, False)

    def test_hashcat_7_multiple_devices(self):
        line = "STATUS\t5\tSPEED\t8947055\t1000\t0\t1000\tEXEC_RUNTIME\t0.062464\t0.000000\tCURKU\t0\tPROGRESS\t9025\t9025\tRECHASH\t0\t1\tRECSALT\t0\t1\tTEMP\t44\t-1\tREJECTED\t0\tUTIL\t46\t-1\tPOWER\t-1\t-1\t"
        status = HashcatStatus(line)
        self.assertTrue(status.is_valid())
        self.assertEqual(status.status, 5)
        self.assertEqual(status.speed, [[8947055, 1000], [0, 1000]])
        self.assertEqual(status.exec_runtime, [0.062464, 0.000000])
        self.assertEqual(status.curku, 0)
        self.assertEqual(status.progress, [9025, 9025])
        self.assertEqual(status.rec_hash, [0, 1])
        self.assertEqual(status.rec_salt, [0, 1])
        self.assertEqual(status.temp, [44, -1])
        self.assertEqual(status.rejected, 0)
        self.assertEqual(status.util, [46, -1])
        self.assertEqual(status.power, [-1, -1])
        self.assertEqual(status.unknown_fields, False)

    def test_valid_status_line(self):
        line = "STATUS\t1\tSPEED\t2534\t1000\tEXEC_RUNTIME\t123\tCURKU\t45\tPROGRESS\t67\t100\tRECHASH\t89\t120\tRECSALT\t56\t110\tTEMP\t25\tREJECTED\t7\tUTIL\t85\t90\tPOWER\t100\t150"
        status = HashcatStatus(line)
        self.assertEqual(status.status, 1)
        self.assertEqual(status.speed, [[2534, 1000]])
        self.assertEqual(status.exec_runtime, [123])
        self.assertEqual(status.curku, 45)
        self.assertEqual(status.progress, [67, 100])
        self.assertEqual(status.rec_hash, [89, 120])
        self.assertEqual(status.rec_salt, [56, 110])
        self.assertEqual(status.temp, [25])
        self.assertEqual(status.rejected, 7)
        self.assertEqual(status.util, [85, 90])
        self.assertEqual(status.power, [100, 150])

    def test_invalid_status_line(self):
        line = "NOT_STATUS_LINE"
        status = HashcatStatus(line)
        self.assertEqual(status.status, -1)

    def test_missing_fields(self):
        line = "STATUS\t1\tSPEED\t200\t1000"
        status = HashcatStatus(line)
        self.assertEqual(status.status, 1)
        self.assertEqual(status.speed, [[200, 1000]])
        self.assertEqual(status.exec_runtime, [])
        self.assertEqual(status.curku, 0)
        self.assertEqual(status.progress, [0, 0])

    def test_get_progress(self):
        line = "STATUS\t1\tPROGRESS\t42\t100"
        status = HashcatStatus(line)
        self.assertEqual(status.get_progress(), 42)

    def test_get_speed(self):
        line = "STATUS\t1\tSPEED\t12400\t1000\t2000\t1000"
        status = HashcatStatus(line)
        self.assertEqual(status.get_speed(), 12400 + 2000)

    def test_get_util(self):
        line = "STATUS\t1\tUTIL\t85\t90"
        status = HashcatStatus(line)
        self.assertEqual(status.get_util(), (85 + 90) // 2)

if __name__ == '__main__':
    unittest.main()
