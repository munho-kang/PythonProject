"""
연합학습을 위한 데이터 분할 스크립트
autonomous_robot_dataset.csv를 여러 워커용으로 분할

각 워커가 서로 다른 데이터를 가지도록 분할 (Non-IID 시뮬레이션 가능)
"""
import pandas as pd
import numpy as np
import argparse
import os


def split_iid(df, num_workers):
    """
    IID (Independent and Identically Distributed) 분할
    데이터를 무작위로 균등하게 분할
    """
    print(f"IID 분할: {len(df)}개 샘플을 {num_workers}개 워커로 분할")

    # 무작위 섞기
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # 균등 분할
    splits = np.array_split(df_shuffled, num_workers)

    for i, split in enumerate(splits):
        print(f"  워커 {i + 1}: {len(split)} 샘플")

    return splits


def split_non_iid_by_class(df, num_workers, target_col='target'):
    """
    Non-IID 분할: 클래스별로 다르게 분할
    각 워커가 특정 클래스에 편향된 데이터를 가짐
    """
    print(f"Non-IID 분할 (클래스 편향): {len(df)}개 샘플을 {num_workers}개 워커로 분할")

    classes = df[target_col].unique()
    print(f"  클래스: {classes}")

    # 각 워커에게 주요 클래스 할당
    worker_data = [[] for _ in range(num_workers)]

    for i, cls in enumerate(classes):
        # 해당 클래스 데이터 추출
        class_data = df[df[target_col] == cls]

        # 주요 워커 (70%) + 나머지 워커들 (30%)
        main_worker = i % num_workers

        # 섞기
        class_data_shuffled = class_data.sample(frac=1, random_state=42).reset_index(drop=True)

        split_point = int(len(class_data_shuffled) * 0.7)

        # 주요 워커에게 70%
        worker_data[main_worker].append(class_data_shuffled[:split_point])

        # 나머지 30%는 다른 워커들에게 분배
        remaining = class_data_shuffled[split_point:]
        remaining_splits = np.array_split(remaining, num_workers - 1)

        j = 0
        for w in range(num_workers):
            if w != main_worker:
                worker_data[w].append(remaining_splits[j])
                j += 1

    # 각 워커 데이터 합치기
    final_splits = []
    for i, data_list in enumerate(worker_data):
        worker_df = pd.concat(data_list, ignore_index=True)
        worker_df = worker_df.sample(frac=1, random_state=42).reset_index(drop=True)
        final_splits.append(worker_df)

        # 클래스 분포 출력
        print(f"\n  워커 {i + 1}: {len(worker_df)} 샘플")
        for cls in classes:
            count = len(worker_df[worker_df[target_col] == cls])
            pct = count / len(worker_df) * 100 if len(worker_df) > 0 else 0
            print(f"    {cls}: {count} ({pct:.1f}%)")

    return final_splits


def split_non_iid_by_quantity(df, num_workers):
    """
    Non-IID 분할: 데이터 양이 불균등
    실제 환경에서 각 노드가 서로 다른 양의 데이터를 가진 상황 시뮬레이션
    """
    print(f"Non-IID 분할 (데이터 양 불균등): {len(df)}개 샘플을 {num_workers}개 워커로 분할")

    # 무작위 비율 생성 (디리클레 분포 사용)
    alpha = 0.5  # 낮을수록 불균등
    proportions = np.random.dirichlet([alpha] * num_workers)

    # 섞기
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # 비율에 따라 분할
    splits = []
    start_idx = 0

    for i, prop in enumerate(proportions):
        num_samples = int(len(df_shuffled) * prop)

        if i == num_workers - 1:  # 마지막 워커는 남은 모든 데이터
            split = df_shuffled[start_idx:]
        else:
            split = df_shuffled[start_idx:start_idx + num_samples]

        splits.append(split)
        print(f"  워커 {i + 1}: {len(split)} 샘플 ({prop * 100:.1f}%)")
        start_idx += num_samples

    return splits


def save_splits(splits, output_dir, prefix="worker"):
    """분할된 데이터 저장"""
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n파일 저장 중: {output_dir}")

    for i, split in enumerate(splits):
        filename = f"{prefix}_{i + 1}_data.csv"
        filepath = os.path.join(output_dir, filename)
        split.to_csv(filepath, index=False)
        print(f"  ✅ {filename} ({len(split)} 샘플)")

    print(f"\n총 {len(splits)}개 파일 저장 완료")


def main():
    ap = argparse.ArgumentParser(description="연합학습용 데이터 분할")
    ap.add_argument("--input", default="autonomous_robot_dataset.csv",
                    help="입력 CSV 파일")
    ap.add_argument("--output-dir", default="federated_data",
                    help="출력 디렉토리")
    ap.add_argument("--num-workers", type=int, default=2,
                    help="워커 수")
    ap.add_argument("--split-method", choices=['iid', 'non-iid-class', 'non-iid-quantity'],
                    default='iid', help="분할 방법")
    args = ap.parse_args()

    print("=" * 70)
    print("연합학습용 데이터 분할")
    print("=" * 70)
    print(f"입력: {args.input}")
    print(f"워커 수: {args.num_workers}")
    print(f"분할 방법: {args.split_method}")
    print()

    # 데이터 로드
    if not os.path.exists(args.input):
        print(f"❌ 파일을 찾을 수 없습니다: {args.input}")
        return

    df = pd.read_csv(args.input)
    print(f"전체 데이터: {len(df)} 샘플")
    print(f"컬럼: {df.columns.tolist()}")
    print()

    # 분할
    if args.split_method == 'iid':
        splits = split_iid(df, args.num_workers)
    elif args.split_method == 'non-iid-class':
        splits = split_non_iid_by_class(df, args.num_workers)
    elif args.split_method == 'non-iid-quantity':
        splits = split_non_iid_by_quantity(df, args.num_workers)

    # 저장
    save_splits(splits, args.output_dir)

    print()
    print("=" * 70)
    print("✨ 완료!")
    print("=" * 70)
    print(f"\n각 워커에서 다음과 같이 실행하세요:")
    for i in range(args.num_workers):
        filename = f"worker_{i + 1}_data.csv"
        print(f"\n워커 {i + 1}:")
        print(f"  python3 federated_worker.py \\")
        print(f"    --node-id worker_{i + 1} \\")
        print(f"    --server-ip 194.168.1.29 \\")
        print(f"    --data {args.output_dir}/{filename}")


if __name__ == "__main__":
    main()