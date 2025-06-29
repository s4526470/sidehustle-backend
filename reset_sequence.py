from sqlalchemy import text
from database import engine  # 确保导入你的 SQLAlchemy engine

def reset_post_id_sequence():
    with engine.connect() as conn:
        try:
            # 获取当前最大 id
            result = conn.execute(text("SELECT MAX(id) FROM posts"))
            max_id = result.scalar() or 0

            # 获取自动序列名称
            result = conn.execute(text("SELECT pg_get_serial_sequence('posts', 'id')"))
            sequence_name = result.scalar()

            if not sequence_name:
                print("无法获取序列名，检查表名和字段是否正确。")
                return

            # 重置序列值为最大 id
            conn.execute(text(f"SELECT setval(:seq_name, :max_id)"), {"seq_name": sequence_name, "max_id": max_id})
            print(f"已将序列 {sequence_name} 重置为 {max_id}")
        except Exception as e:
            print("重置序列时出错：", e)

if __name__ == "__main__":
    reset_post_id_sequence()
