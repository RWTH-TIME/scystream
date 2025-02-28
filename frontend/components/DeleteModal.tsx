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
      <div className="flex justify-end mt-5">
        <button
          type="button"
          onClick={onClose}
          className="w-[78px] h-[36px] px-4 py-2 mr-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
        >
          Cancel
        </button>
        <button
          className="flex flex-col w-[78px] h-[36px] px-4 py-2 text-white bg-red-500 rounded hover:bg-red-600"
          disabled={loading}
          onClick={() => onDelete()}
        >
          <LoadingAndError loading={loading} iconSize={21}>
            Delete
          </LoadingAndError>
        </button>
      </div>

    </Modal>

  )
}
