# numerical imports
import torch
import numpy as np

# Import base class
from LION.optimizers.LIONsolver import LIONsolver

# standard imports
from tqdm import tqdm


class SupervisedSolver(LIONsolver):
    def __init__(
        self,
        model,
        optimizer,
        loss_fn,
        save_folder,
        final_result_fname,
        verbose=False,
        device=torch.device(f"cuda:{torch.cuda.current_device()}"),
        model_regularization=None,
    ):
        super().__init__(
            model,
            optimizer,
            loss_fn,
            save_folder,
            final_result_fname,
            verbose=verbose,
            device=device,
            model_regularization=model_regularization,
        )

    def mini_batch_step(self, data, target):
        """
        This function isresponsible for performing a single mini-batch step of the optimization.
        returns the loss of the mini-batch
        """
        # set model to train
        self.model.train()
        # Zero gradients
        self.optimizer.zero_grad()
        # Forward pass
        output = self.model(data)
        # Compute loss
        if self.model_regularization is not None:
            self.loss = self.loss_fn(output, target) + self.model_regularization(
                self.model
            )
        else:
            self.loss = self.loss_fn(output, target)
        # Update optimizer and model
        self.loss.backward()
        self.optimizer.step()
        return self.loss.item()

    def train_step(self):
        """
        This function is responsible for performing a single tranining set epoch of the optimization.
        returns the average loss of the epoch
        """
        self.model.train()
        epoch_loss = 0.0
        for index, (data, target) in enumerate(self.train_loader):
            epoch_loss += self.mini_batch_step(
                data.to(self.device), target.to(self.device)
            )
        return epoch_loss / len(self.train_loader)

    def validate(self):
        """
        This function is responsible for performing a single validation set of the optimization.
        returns the average loss of the validation set this epoch.
        """
        # not a fan of using sentinel values like this, change for either ENUM or something like that
        assert (
            self.check_validation_ready() == 0
        ), "Solver not ready for validation. Please call set_validation."

        # these always pass if the above does, this is just to placate static type checker
        assert self.validation_loader is not None
        assert self.validation_fn is not None

        status = self.model.training
        self.model.eval()
        validation_loss = 0.0
        if self.verbose:
            print("Validating...")
        for _, (data, target) in tqdm(
            enumerate(self.validation_loader), disable=True
        ):
            with torch.no_grad():
                output = self.model(data.to(self.device))
                validation_loss = self.validation_fn(output, target.to(self.device))

        # return to train if it was in train
        if status:
            self.model.train()
        return validation_loss / len(self.validation_loader)

    def epoch_step(self, epoch):
        """
        This function is responsible for performing a single epoch of the optimization.
        """
        self.train_loss[epoch] = self.train_step()
        # actually make sure we're doing validation
        if (epoch + 1) % self.validation_freq == 0 and self.validation_loss is not None:
            self.validation_loss[epoch] = self.validate()
            if self.verbose:
                print(
                    f"Epoch {epoch+1} - Training loss: {self.train_loss[epoch]} - Validation loss: {self.validation_loss[epoch]}"
                )

            if self.validation_fname is not None and self.validation_loss[
                epoch
            ] <= np.min(self.validation_loss[np.nonzero(self.validation_loss)]):
                self.save_validation(epoch)
        elif self.verbose:
            print(f"Epoch {epoch+1} - Training loss: {self.train_loss[epoch]}")
        # elif self.validation_freq is not None:
        #     self.validation_loss[epoch] = self.validate()

    def train(self, n_epochs):
        """
        This function is responsible for performing the optimization.
        """
        assert n_epochs > 0, "Number of epochs must be a positive integer"
        # Make sure all parameters are set
        self.check_complete()

        self.current_epoch = n_epochs

        self.train_loss = np.zeros(self.current_epoch)
        if self.validation_fn is not None:
            self.validation_loss = np.zeros(self.current_epoch)

        init_epoch = 0
        if self.do_load_checkpoint:
            init_epoch = self.load_checkpoint()

        # train loop
        for epoch in tqdm(range(init_epoch, self.current_epoch)):
            self.epoch_step(epoch)
            if (epoch + 1) % self.checkpoint_freq == 0:
                self.save_checkpoint(epoch)
