from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from datasets import Dataset, load_dataset
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
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


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output-dir",
        default="ml_models/berturk-mide22",
    )

    parser.add_argument(
        "--epochs",
        type=float,
        default=3,
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
        help="Smoke test için örneğin 300 verilebilir.",
    )

    return parser.parse_args()


def load_mide22(max_samples: int | None):
    print("MiDe22 indiriliyor...")

    dataset = load_dataset(
        "ogozcelik/turkish-fake-news-detection",
        split="train",
    )

    frame = dataset.to_pandas()

    frame = frame[
        frame["label"].isin(SOURCE_LABEL_MAP)
    ].copy()

    frame["target_name"] = frame["label"].map(
        SOURCE_LABEL_MAP
    )

    frame["labels"] = frame["target_name"].map(
        LABEL2ID
    )

    frame = frame[
        ["tweet", "labels", "target_name"]
    ].dropna()

    if max_samples is not None:
        sample_count = min(
            max_samples,
            len(frame),
        )

        frame = frame.sample(
            n=sample_count,
            random_state=42,
        )

    train_frame, validation_frame = train_test_split(
        frame,
        test_size=0.2,
        random_state=42,
        stratify=frame["labels"],
    )

    print()
    print("Train:", len(train_frame))
    print("Validation:", len(validation_frame))
    print()
    print("Train class counts:")
    print(train_frame["target_name"].value_counts())

    return (
        Dataset.from_pandas(
            train_frame,
            preserve_index=False,
        ),
        Dataset.from_pandas(
            validation_frame,
            preserve_index=False,
        ),
    )


def compute_metrics(eval_prediction):
    logits, labels = eval_prediction

    predictions = np.argmax(
        logits,
        axis=-1,
    )

    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            average="macro",
            zero_division=0,
        )
    )

    accuracy = accuracy_score(
        labels,
        predictions,
    )

    return {
        "accuracy": accuracy,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
    }


def main():
    args = parse_args()

    output_dir = Path(args.output_dir)

    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL
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

    train_dataset, validation_dataset = (
        load_mide22(
            max_samples=args.max_samples,
        )
    )

    def tokenize(batch):
        return tokenizer(
            batch["tweet"],
            truncation=True,
            max_length=args.max_length,
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

    data_collator = DataCollatorWithPadding(
        tokenizer=tokenizer
    )

    training_args = TrainingArguments(
        output_dir="training_outputs/berturk-mide22",
        learning_rate=2e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        warmup_ratio=0.1,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        logging_steps=25,
        report_to="none",
        seed=42,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print()
    print("Eğitim başlıyor...")
    print()

    trainer.train()

    print()
    print("Validation değerlendirmesi:")
    print()

    metrics = trainer.evaluate()

    for key, value in metrics.items():
        print(f"{key}: {value}")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    print()
    print(
        f"Model kaydedildi: {output_dir.resolve()}"
    )


if __name__ == "__main__":
    main()
