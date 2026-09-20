from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from datasets import Dataset, load_dataset
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)


BASE_MODEL = "dbmdz/bert-base-turkish-cased"

LABEL2ID = {
    "gercek": 0,
    "sahte": 1,
    "belirsiz": 2,
}

ID2LABEL = {
    0: "gercek",
    1: "sahte",
    2: "belirsiz",
}

SOURCE_LABEL_MAP = {
    "True": "gercek",
    "False": "sahte",
    "Other": "belirsiz",
}


class WeightedTrainer(Trainer):
    def __init__(
        self,
        *args,
        class_weights: torch.Tensor | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(
        self,
        model,
        inputs,
        return_outputs=False,
        num_items_in_batch=None,
    ):
        labels = inputs.get("labels")

        outputs = model(**inputs)
        logits = outputs.get("logits")

        weights = None

        if self.class_weights is not None:
            weights = self.class_weights.to(
                logits.device
            )

        loss_function = torch.nn.CrossEntropyLoss(
            weight=weights
        )

        loss = loss_function(
            logits,
            labels,
        )

        return (
            (loss, outputs)
            if return_outputs
            else loss
        )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output-dir",
        default="ml_models/berturk-mide22",
    )

    parser.add_argument(
        "--epochs",
        type=float,
        default=5,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--max-length",
        type=int,
        default=256,
    )

    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help=(
            "Smoke test için örneğin "
            "300 verilebilir."
        ),
    )

    return parser.parse_args()


def prepare_dataframe(
    max_samples: int | None,
) -> pd.DataFrame:
    print("MiDe22 yükleniyor...")

    dataset = load_dataset(
        "ogozcelik/turkish-fake-news-detection",
        split="train",
    )

    frame = dataset.to_pandas()

    frame = frame[
        frame["label"].isin(
            SOURCE_LABEL_MAP
        )
    ].copy()

    frame["target_name"] = (
        frame["label"].map(
            SOURCE_LABEL_MAP
        )
    )

    frame["labels"] = (
        frame["target_name"].map(
            LABEL2ID
        )
    )

    frame = frame[
        [
            "tweet",
            "labels",
            "target_name",
        ]
    ].dropna()

    frame["labels"] = (
        frame["labels"].astype(int)
    )

    if (
        max_samples is not None
        and max_samples < len(frame)
    ):
        per_class = max_samples // len(LABEL2ID)

        sampled_frames = []

        for label_id in sorted(LABEL2ID.values()):
            class_frame = frame[
                frame["labels"] == label_id
            ]

            sample_count = min(
                per_class,
                len(class_frame),
            )

            sampled_frames.append(
                class_frame.sample(
                    n=sample_count,
                    random_state=42,
                )
            )

        frame = pd.concat(
            sampled_frames,
            ignore_index=True,
        )

        frame = frame.sample(
            frac=1.0,
            random_state=42,
        )

    frame = frame.reset_index(drop=True)

    return frame


def split_dataset(
    frame: pd.DataFrame,
):
    train_frame, temp_frame = (
        train_test_split(
            frame,
            test_size=0.30,
            random_state=42,
            stratify=frame["labels"],
        )
    )

    validation_frame, test_frame = (
        train_test_split(
            temp_frame,
            test_size=0.50,
            random_state=42,
            stratify=temp_frame["labels"],
        )
    )

    return (
        train_frame.reset_index(
            drop=True
        ),
        validation_frame.reset_index(
            drop=True
        ),
        test_frame.reset_index(
            drop=True
        ),
    )


def print_distribution(
    name: str,
    frame: pd.DataFrame,
):
    print()
    print(
        f"{name}: {len(frame)} örnek"
    )

    print(
        frame[
            "target_name"
        ].value_counts()
    )


def calculate_class_weights(
    train_frame: pd.DataFrame,
) -> torch.Tensor:
    classes = np.array(
        [
            LABEL2ID["gercek"],
            LABEL2ID["sahte"],
            LABEL2ID["belirsiz"],
        ]
    )

    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=train_frame[
            "labels"
        ].to_numpy(),
    )

    print()
    print("Class weights:")

    for class_id, weight in zip(
        classes,
        weights,
    ):
        print(
            f"  {ID2LABEL[class_id]}: "
            f"{weight:.4f}"
        )

    return torch.tensor(
        weights,
        dtype=torch.float32,
    )


def compute_metrics(
    eval_prediction,
):
    logits, labels = eval_prediction

    predictions = np.argmax(
        logits,
        axis=-1,
    )

    accuracy = accuracy_score(
        labels,
        predictions,
    )

    (
        precision,
        recall,
        f1,
        _,
    ) = precision_recall_fscore_support(
        labels,
        predictions,
        average="macro",
        zero_division=0,
    )

    return {
        "accuracy": float(
            accuracy
        ),
        "precision_macro": float(
            precision
        ),
        "recall_macro": float(
            recall
        ),
        "f1_macro": float(
            f1
        ),
    }


def save_test_results(
    trainer: Trainer,
    test_dataset: Dataset,
    output_dir: Path,
):
    print()
    print("=" * 60)
    print("TEST SET DEĞERLENDİRMESİ")
    print("=" * 60)

    prediction_output = trainer.predict(
        test_dataset
    )

    logits = (
        prediction_output.predictions
    )

    labels = (
        prediction_output.label_ids
    )

    predictions = np.argmax(
        logits,
        axis=-1,
    )

    report = classification_report(
        labels,
        predictions,
        labels=[0, 1, 2],
        target_names=[
            "gercek",
            "sahte",
            "belirsiz",
        ],
        output_dict=True,
        zero_division=0,
    )

    print()
    print(
        classification_report(
            labels,
            predictions,
            labels=[0, 1, 2],
            target_names=[
                "gercek",
                "sahte",
                "belirsiz",
            ],
            zero_division=0,
        )
    )

    matrix = confusion_matrix(
        labels,
        predictions,
        labels=[0, 1, 2],
    )

    matrix_frame = pd.DataFrame(
        matrix,
        index=[
            "actual_gercek",
            "actual_sahte",
            "actual_belirsiz",
        ],
        columns=[
            "pred_gercek",
            "pred_sahte",
            "pred_belirsiz",
        ],
    )

    print("Confusion Matrix:")
    print(matrix_frame)

    evaluation_dir = (
        output_dir
        / "evaluation"
    )

    evaluation_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with (
        evaluation_dir
        / "classification_report.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    matrix_frame.to_csv(
        evaluation_dir
        / "confusion_matrix.csv",
        encoding="utf-8",
    )

    test_metrics = {
        key: float(value)
        for key, value
        in prediction_output.metrics.items()
        if isinstance(
            value,
            (int, float),
        )
    }

    with (
        evaluation_dir
        / "test_metrics.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            test_metrics,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(
        "Değerlendirme çıktıları:"
    )
    print(
        evaluation_dir.resolve()
    )


def main():
    args = parse_args()

    print()
    print("=" * 60)
    print(
        "BERTurk MiDe22 Training Pipeline"
    )
    print("=" * 60)

    print()
    print(
        "Device:",
        "CUDA"
        if torch.cuda.is_available()
        else "CPU",
    )

    if torch.cuda.is_available():
        print(
            "GPU:",
            torch.cuda.get_device_name(0),
        )

    frame = prepare_dataframe(
        max_samples=args.max_samples,
    )

    (
        train_frame,
        validation_frame,
        test_frame,
    ) = split_dataset(frame)

    print()
    print(
        f"Toplam veri: {len(frame)}"
    )

    print_distribution(
        "Train",
        train_frame,
    )

    print_distribution(
        "Validation",
        validation_frame,
    )

    print_distribution(
        "Test",
        test_frame,
    )

    class_weights = (
        calculate_class_weights(
            train_frame
        )
    )

    print()
    print(
        "Tokenizer yükleniyor..."
    )

    tokenizer = (
        AutoTokenizer.from_pretrained(
            BASE_MODEL
        )
    )

    print(
        "BERTurk modeli yükleniyor..."
    )

    model = (
        AutoModelForSequenceClassification
        .from_pretrained(
            BASE_MODEL,
            num_labels=3,
            id2label=ID2LABEL,
            label2id=LABEL2ID,
        )
    )

    def tokenize(batch):
        return tokenizer(
            batch["tweet"],
            truncation=True,
            max_length=args.max_length,
        )

    train_dataset = (
        Dataset.from_pandas(
            train_frame,
            preserve_index=False,
        )
    )

    validation_dataset = (
        Dataset.from_pandas(
            validation_frame,
            preserve_index=False,
        )
    )

    test_dataset = (
        Dataset.from_pandas(
            test_frame,
            preserve_index=False,
        )
    )

    train_dataset = train_dataset.map(
        tokenize,
        batched=True,
    )

    validation_dataset = (
        validation_dataset.map(
            tokenize,
            batched=True,
        )
    )

    test_dataset = test_dataset.map(
        tokenize,
        batched=True,
    )

    data_collator = (
        DataCollatorWithPadding(
            tokenizer=tokenizer
        )
    )

    training_output_dir = (
        Path(
            "training_outputs"
        )
        / "berturk-mide22"
    )

    training_args = TrainingArguments(
        output_dir=str(
            training_output_dir
        ),
        learning_rate=2e-5,
        per_device_train_batch_size=(
            args.batch_size
        ),
        per_device_eval_batch_size=(
            args.batch_size
        ),
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        warmup_ratio=0.1,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=25,
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        save_total_limit=2,
        report_to="none",
        seed=42,
        data_seed=42,
        fp16=torch.cuda.is_available(),
        dataloader_pin_memory=(
            torch.cuda.is_available()
        ),
    )

    trainer = WeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        class_weights=class_weights,
        callbacks=[
            EarlyStoppingCallback(
                early_stopping_patience=2
            )
        ],
    )

    print()
    print("=" * 60)
    print("EĞİTİM BAŞLIYOR")
    print("=" * 60)

    trainer.train()

    print()
    print("=" * 60)
    print(
        "VALIDATION SONUÇLARI"
    )
    print("=" * 60)

    validation_metrics = (
        trainer.evaluate()
    )

    for key, value in (
        validation_metrics.items()
    ):
        print(
            f"{key}: {value}"
        )

    output_dir = Path(
        args.output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    trainer.save_model(
        output_dir
    )

    tokenizer.save_pretrained(
        output_dir
    )

    save_test_results(
        trainer=trainer,
        test_dataset=test_dataset,
        output_dir=output_dir,
    )

    print()
    print("=" * 60)
    print(
        "EĞİTİM TAMAMLANDI"
    )
    print("=" * 60)

    print()
    print(
        "Model:",
        output_dir.resolve(),
    )


if __name__ == "__main__":
    main()
