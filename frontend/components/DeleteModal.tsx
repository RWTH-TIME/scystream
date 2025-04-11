import Button, { ButtonSentiment } from "./Button"
import LoadingAndError from "./LoadingAndError"
import Modal, { type ModalProps } from "./Modal"

type DeleteModal = Omit<ModalProps, "children"> & {
  onDelete: () => void,
  loading: boolean,
  header: string,
  desc?: string,
};

export default function DeleteModal({
  isOpen,
  onClose,
  className = "",
  onDelete,
  loading,
  header,
  desc
}: DeleteModal) {
  return (
    <Modal className={className} isOpen={isOpen} onClose={onClose}>
      <h2 className="text-xl font-bold">{header}</h2>
      {desc}
      <div className="flex justify-between mt-5">
        <Button
          type="button"
          onClick={onClose}
          sentiment={ButtonSentiment.NEUTRAL}
        >
          Cancel
        </Button>
        <Button
          disabled={loading}
          onClick={() => onDelete()}
          sentiment={ButtonSentiment.NEGATIVE}
        >
          <LoadingAndError loading={loading} iconSize={21}>
            Delete
          </LoadingAndError>
        </Button>
      </div>
    </Modal>
  )
}
