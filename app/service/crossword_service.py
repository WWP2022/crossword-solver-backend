import json
import os
import shutil

from PIL import Image

import app.clients.minio_client as minio_client
import app.repository.crossword_repository as crossword_repository
import app.repository.crossword_task_repository as crossword_task_repository
from app.model.database.crossword_info import CrosswordInfo, CrosswordStatus, CrosswordSolvingMessage
from app.model.database.crossword_task import CrosswordTask
from app.processing.extract_crossword import extract_crossword
from app.processing.result_image import create_result_image
from app.service import crossword_clue_service


def remove_unnecessary_files(base_image_path: str):
    shutil.rmtree(base_image_path, ignore_errors=True)


def add_crossword_task(file_stream, user_id: str, crossword_name: str, timestamp: str):
    crossword_info = CrosswordInfo(
        user_id=user_id,
        crossword_name=crossword_name,
        timestamp=timestamp
    )
    crossword_info = crossword_repository.save_crossword_info(crossword_info)

    img = Image.open(file_stream)
    img = img.convert("RGB")

    base_image_path = f'/tmp/{user_id}/{crossword_info.id}/'
    unprocessed_image_path = base_image_path + "unprocessed.jpg"
    remove_unnecessary_files(base_image_path)
    os.makedirs(base_image_path, exist_ok=True)
    img.save(unprocessed_image_path, quality=100)

    crossword_task = CrosswordTask(
        crossword_info_id=crossword_info.id,
        unprocessed_image_path=unprocessed_image_path,
        base_image_path=base_image_path,
        user_id=user_id
    )
    return crossword_task_repository.save_crossword_task(crossword_task)


def get_crossword_info_by_crossword_id(crossword_id: int):
    return crossword_repository.find_crossword_info_by_crossword_id(crossword_id)


def get_crossword_processed_image(user_id: str, crossword_id: int):
    crossword_info = crossword_repository.find_crossword_info_by_crossword_id(crossword_id)
    if crossword_info is None:
        return None
    return minio_client.get_processed_image(user_id, crossword_info.id)


def get_crossword_processed_images_ids_names_and_timestamps_by_user_id(user_id: str):
    crossword_info = crossword_repository.find_crosswords_info_by_user_id(user_id)
    return [{"crossword_id": info.id,
             "crossword_name": info.crossword_name,
             "timestamp": info.timestamp} for info in crossword_info]


def get_number_of_all_crossword_by_user_id(user_id: str):
    return crossword_repository.get_number_crosswords_info_by_user_id(user_id)


def update_crossword(crossword_info: CrosswordInfo, crossword_name, is_accepted=True):
    if is_accepted:
        crossword_clue_service.add_questions_and_answers_from_crossword(crossword_info)
        return crossword_repository.update_crossword(
            crossword_info,
            crossword_name,
            CrosswordStatus.SOLVED_ACCEPTED.value
        )
    minio_client.delete_processed_image(crossword_info)
    return crossword_repository.delete_crossword_info(crossword_info)


def delete_crossword(crossword_info: CrosswordInfo):
    minio_client.delete_processed_image(crossword_info)
    return crossword_repository.delete_crossword_info(crossword_info)


def solve_crossword_if_exist():
    # Check and get solve task is not None
    crossword_task = crossword_task_repository.find_crossword_task()
    if crossword_task is None:
        return

    # Update status from NEW to SOLVING
    crossword_info = crossword_repository.update_crossword_info_status_by_crossword_info_id(
        crossword_task.crossword_info_id,
        CrosswordStatus.SOLVING.value
    )

    # fetching necessary paths and user_id
    base_image_path = crossword_task.base_image_path
    unprocessed_image_path = crossword_task.unprocessed_image_path

    # Extract crossword from image, now we use hardcoded_crossword because ocr is not working
    crossword, solving_message = extract_crossword(unprocessed_image_path, base_image_path)

    # If some troubles during processing set status to CANNOT SOLVE and set info for client
    if solving_message is not CrosswordSolvingMessage.SOLVED_SUCCESSFUL:
        crossword_minio_path = minio_client.put_unprocessed_image_with_error(
            unprocessed_image_path,
            crossword_task.user_id,
            crossword_info.id,
            solving_message.value)

        crossword_repository.update_crossword_after_processing(
            crossword_info=crossword_info,
            status=CrosswordStatus.CANNOT_SOLVE.value,
            minio_path=crossword_minio_path,
            questions_and_answers=json.dumps([]),
            solving_message=solving_message.value
        )

        clean_after_solving_crossword(base_image_path, crossword_task)
        return

    crossword.solve(crossword_task.user_id)

    # TODO helpful method shows solved crossword in backend logs
    # crossword.print_result()

    # Create result image and save crossword image on minio
    processed_local_path = create_result_image(crossword, base_image_path, unprocessed_image_path)
    crossword_minio_path = minio_client.put_processed_image(
        processed_local_path,
        crossword_task.user_id,
        crossword_info.id)

    # Update status to SOLVED and add push image on minio service
    questions_and_answers = [{"question": node.definition, "answer": node.solution} for node in crossword.nodes]
    crossword_repository.update_crossword_after_processing(
        crossword_info,
        CrosswordStatus.SOLVED_WAITING.value,
        crossword_minio_path,
        json.dumps(questions_and_answers),
        solving_message.value
    )
    clean_after_solving_crossword(base_image_path, crossword_task)


def clean_after_solving_crossword(base_image_path: str, crossword_task: CrosswordTask):
    remove_unnecessary_files(base_image_path)
    crossword_task_repository.delete_crossword_task(crossword_task)


def is_crossword_name_exist(user_id, crossword_name):
    return crossword_repository.find_crossword_info_by_crossword_name_and_user_id(crossword_name, user_id) is not None


def get_default_name(user_id: str):
    crossword_info = crossword_repository.find_last_default_name_by_user_id(user_id)
    if crossword_info is None:
        return "Krzyżówka-1"
    new_default_crossword_number = int(crossword_info.crossword_name.split('-')[1]) + 1
    return "Krzyżówka-" + str(new_default_crossword_number)
