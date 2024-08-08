'''
analyzed file table info
+-----------------+--------------+------+-----+---------+-------+
| Field           | Type         | Null | Key | Default | Extra |
+-----------------+--------------+------+-----+---------+-------+
| saved_file_name | varchar(255) | NO   | PRI | NULL    |       |
| created_at      | datetime(6)  | YES  |     | NULL    |       |
| updated_at      | datetime(6)  | YES  |     | NULL    |       |
| content_type    | varchar(255) | NO   |     | NULL    |       |
| file_size       | bigint(20)   | NO   |     | NULL    |       |
| is_passed       | bit(1)       | NO   |     | NULL    |       |
| raw_file_name   | varchar(255) | NO   | UNI | NULL    |       |
| saved_path      | varchar(255) | NO   | UNI | NULL    |       |
+-----------------+--------------+------+-----+---------+-------+
'''
class AnalyzedFile:
    def __init__(
            self, saved_file_name, created_at, updated_at, content_type,
            file_size, is_passed, raw_file_name, saved_path, defect_severity
            ):
        self.saved_file_name = saved_file_name
        self.created_at = created_at
        self.updated_at = updated_at
        self.content_type  = content_type
        self.file_size = file_size
        self.is_passed = is_passed
        self.raw_file_name = raw_file_name
        self.saved_path = saved_path
        self.defect_severity = defect_severity

'''
    raw_file table info
    +-----------------+--------------+------+-----+---------+-------+
    | Field           | Type         | Null | Key | Default | Extra |
    +-----------------+--------------+------+-----+---------+-------+
    | saved_file_name | varchar(255) | NO   | PRI | NULL    |       |
    | created_at      | datetime(6)  | YES  |     | NULL    |       |
    | updated_at      | datetime(6)  | YES  |     | NULL    |       |
    | content_type    | varchar(255) | NO   |     | NULL    |       |
    | file_size       | bigint(20)   | NO   |     | NULL    |       |
    | saved_path      | varchar(255) | NO   | UNI | NULL    |       |
    +-----------------+--------------+------+-----+---------+-------+
'''
class RawFile:
    def __init__(
            self, saved_file_name, created_at, updated_at, 
            content_type, file_size, saved_path
        ):
        self.saved_file_name = saved_file_name
        self.created_at = created_at
        self.updated_at = updated_at
        self.content_type = content_type
        self.file_size = file_size
        self.saved_path = saved_path

'''
inspection table info
+--------------------+--------------+------+-----+---------+----------------+
| Field              | Type         | Null | Key | Default | Extra          |
+--------------------+--------------+------+-----+---------+----------------+
| id                 | bigint(20)   | NO   | PRI | NULL    | auto_increment |
| created_at         | datetime(6)  | YES  |     | NULL    |                |
| updated_at         | datetime(6)  | YES  |     | NULL    |                |
| analyzed_file_name | varchar(255) | NO   | MUL | NULL    |                |
| area               | float        | NO   |     | NULL    |                |
| defect_type        | tinyint(4)   | NO   |     | NULL    |                |
+--------------------+--------------+------+-----+---------+----------------+
'''
class Inspection:
    def __init__(self, created_at, updated_at, analyzed_file_name, area, defect_type):
        self.created_at = created_at
        self.updated_at = updated_at
        self.analyzed_file_name = analyzed_file_name
        self.area = area
        self.defect_type = defect_type

