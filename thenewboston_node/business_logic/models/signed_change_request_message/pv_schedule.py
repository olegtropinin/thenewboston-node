from dataclasses import dataclass

from thenewboston_node.business_logic.exceptions import ValidationError
from thenewboston_node.business_logic.models.base import BaseDataclass
from thenewboston_node.core.utils.dataclass import cover_docstring, revert_docstring

from .base import SignedChangeRequestMessage


@revert_docstring
@dataclass
@cover_docstring
class PrimaryValidatorSchedule(BaseDataclass):
    begin_block_number: int
    end_block_number: int

    def is_schedule_in_future(self, block_number):
        return block_number < self.begin_block_number

    def is_block_number_included(self, block_number):
        return self.begin_block_number <= block_number <= self.end_block_number

    def is_schedule_at_present(self, block_number):
        return self.is_block_number_included(block_number)

    def is_schedule_in_past(self, block_number):
        return self.end_block_number < block_number

    def validate(self):
        if self.begin_block_number > self.end_block_number:
            raise ValidationError('Begin block number must be less or equal than end block number')


@revert_docstring
@dataclass
@cover_docstring
class PrimaryValidatorScheduleSignedChangeRequestMessage(SignedChangeRequestMessage):
    primary_validator_schedule: PrimaryValidatorSchedule

    def validate(self):
        self.primary_validator_schedule.validate()
